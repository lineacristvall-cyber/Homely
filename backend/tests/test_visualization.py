import base64
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from PIL import Image

from backend import visualization as visual


def png(color):
    output = io.BytesIO()
    Image.new("RGB", (32, 24), color).save(output, "PNG")
    return output.getvalue()


class FitTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"dimensions": {"widthIn": 20, "depthIn": 22, "armHeightIn": 25}}
        self.brief = {"itemType": "dining chairs", "quantity": 6,
                      "measurements": {"roomWidthIn": 120, "roomDepthIn": 100, "tableUndersideIn": 27}}

    def test_positive_legacy_clearance_cannot_qualify_fit(self):
        result = visual.check_numeric_fit(self.candidate, self.brief)
        self.assertEqual(result["fitStatus"], "unknown")
        self.assertTrue(all(check["status"] == "pass" for check in result["fitChecks"]))
        self.assertEqual(result["fitChecks"][2]["clearanceIn"], 2)
        self.assertIn("quantity", result["fitReason"])
        self.assertIn("not verified", result["fitReason"])

    def test_strict_gate_controls_visualization_fit_and_preserves_evidence(self):
        from backend.tests.test_fit import dining
        brief, candidate = dining()
        result = visual.check_numeric_fit(candidate, brief)
        self.assertEqual(result["fitStatus"], "pass")
        self.assertIn("not a guarantee", result["fitScope"])
        check = next(c for c in result["fitChecks"] if c["name"] == "arm.apron")
        self.assertEqual(check["status"], "pass")
        self.assertIn("candidate", check["evidence"])
        candidate["fitEvidence"]["dimensions"]["armHeight"]["value"] = 27
        self.assertEqual(visual.check_numeric_fit(candidate, brief)["fitStatus"], "fail")
        candidate["fitEvidence"]["dimensions"]["width"]["status"] = "conflicting"
        result = visual.check_numeric_fit(candidate, brief)
        self.assertEqual(result["fitStatus"], "unknown")
        self.assertIn("candidate.width", result["fitReason"])

    def test_incomplete_strict_setup_never_falls_back_to_legacy_pass(self):
        for fit in (None, {}, {"schemaVersion": 1}):
            with self.subTest(fit=fit):
                self.brief["fit"] = fit
                result = visual.check_numeric_fit(self.candidate, self.brief)
                self.assertEqual(result["fitStatus"], "unknown")
                self.assertIn("fitScope", result)

    def test_touching_arm_is_not_clearance(self):
        self.brief["measurements"]["tableUndersideIn"] = 25
        self.assertEqual(visual.check_numeric_fit(self.candidate, self.brief)["fitStatus"], "fail")

    def test_missing_stays_unknown_even_when_other_checks_pass(self):
        del self.brief["measurements"]["roomDepthIn"]
        result = visual.check_numeric_fit(self.candidate, self.brief)
        self.assertEqual(result["fitStatus"], "unknown")
        self.assertIsNone(result["fitChecks"][1]["clearanceIn"])

    def test_known_failure_beats_other_unknowns(self):
        self.brief["measurements"] = {"tableUndersideIn": 24}
        self.assertEqual(visual.check_numeric_fit(self.candidate, self.brief)["fitStatus"], "fail")

    def test_invalid_numbers_never_become_measurements(self):
        for invalid in [None, 0, -1, float("inf"), float("nan"), True, "120"]:
            with self.subTest(invalid=invalid):
                self.brief["measurements"]["roomWidthIn"] = invalid
                result = visual.check_numeric_fit(self.candidate, self.brief)
                self.assertIsNone(result["fitChecks"][0]["limitIn"])
                self.assertEqual(result["fitStatus"], "unknown")

    def test_conflicting_arm_measurements_cannot_pass(self):
        self.brief["measurements"]["chairArmIn"] = 24
        result = visual.check_numeric_fit(self.candidate, self.brief)
        self.assertEqual(result["fitStatus"], "unknown")
        self.assertIn("disagree", result["fitChecks"][2]["reason"])

    def test_room_bounds_do_not_assume_rotation(self):
        self.candidate["dimensions"]["widthIn"] = 121
        self.assertEqual(visual.check_numeric_fit(self.candidate, self.brief)["fitStatus"], "fail")

    def test_malformed_measurement_containers_stay_unknown(self):
        self.candidate["dimensions"] = "dimensions not supplied"
        self.brief["measurements"] = []
        self.assertEqual(visual.check_numeric_fit(self.candidate, self.brief)["fitStatus"], "unknown")


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.room, self.product, self.output = [self.root / n for n in ("room.png", "product.png", "output.png")]
        self.room.write_bytes(png("white"))
        self.product.write_bytes(png("brown"))
        self.candidate = {"id": "chair-1", "exactSku": "brown-42", "variant": {"finish": "walnut"},
                          "url": "https://example.com/product", "sourceImageUrl": "/assets/product.png",
                          "sourceRefs": [{"url": "https://example.com/product", "method": "upload"}],
                          "productImageRightsConfirmed": True, "dimensions": {"widthIn": 20}}
        self.brief = {"roomConsent": True, "roomImageUrl": "/assets/room.png", "itemType": "chairs"}
        self.key = "sk-test-" + "x" * 20

    def create(self, key=None):
        return visual.create_visualization(self.room, self.product, self.candidate, self.brief, key, self.output)

    def test_no_key_preserves_source_lineage_without_fake_composite(self):
        with patch.object(visual, "_edit") as call:
            result = self.create()
        call.assert_not_called()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["identityStatus"], "not_generated")
        self.assertEqual(result["fitStatus"], "unknown")
        self.assertIsNone(result["imageUrl"])
        self.assertFalse(self.output.exists())
        self.assertEqual(result["lineage"]["productSha256"], hashlib.sha256(self.product.read_bytes()).hexdigest())
        self.assertEqual(result["sourceImageUrl"], "/assets/product.png")
        self.assertEqual(result["lineage"]["exactSku"], "brown-42")
        self.candidate["variant"]["finish"] = "oak"
        self.assertEqual(result["lineage"]["variant"]["finish"], "walnut")

    def test_consent_and_rights_are_strict_boolean_gates(self):
        with patch.object(visual, "_edit") as call:
            for bad in (None, False, 1, "true"):
                self.brief["roomConsent"] = bad
                with self.assertRaises(ValueError):
                    self.create(self.key)
                self.brief["roomConsent"] = True
                self.candidate["productImageRightsConfirmed"] = bad
                with self.assertRaises(ValueError):
                    self.create(self.key)
                self.candidate["productImageRightsConfirmed"] = True
        call.assert_not_called()

    def test_missing_candidate_or_invalid_image_blocks_provider(self):
        with patch.object(visual, "_edit") as call:
            del self.candidate["id"]
            with self.assertRaises(ValueError):
                self.create(self.key)
            self.candidate["id"] = "chair-1"
            self.product.write_bytes(b"not an image")
            with self.assertRaises(ValueError):
                self.create(self.key)
        call.assert_not_called()

    def test_cannot_overwrite_original_or_prior_output(self):
        self.output = self.room
        with self.assertRaises(ValueError):
            self.create(self.key)
        self.assertEqual(self.room.read_bytes(), png("white"))

    def test_generated_image_is_still_illustrative_and_identity_unverified(self):
        generated = png("blue")
        with patch.object(visual, "_edit", return_value={"data": [{"b64_json": base64.b64encode(generated).decode()}]}) as call:
            result = self.create(self.key)
        self.assertEqual(result["status"], "generated")
        self.assertTrue(result["illustrative"])
        self.assertEqual(result["identityStatus"], "unverified")
        self.assertEqual(result["fitStatus"], "unknown")
        self.assertEqual(self.output.read_bytes(), generated)
        self.assertEqual(self.room.read_bytes(), png("white"))
        self.assertEqual(self.product.read_bytes(), png("brown"))
        self.assertEqual(call.call_args.args[0][0], self.room.read_bytes())
        self.assertEqual(call.call_args.args[1][0], self.product.read_bytes())

    def test_failed_provider_never_leaks_error_or_key(self):
        failure = urllib.error.HTTPError("https://api.openai.com", 401, self.key, None, None)
        with patch.object(visual, "_edit", side_effect=failure) as call:
            result = self.create(self.key)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["errorCode"], "image_provider_authentication")
        self.assertNotIn(self.key, str(result))
        self.assertFalse(self.output.exists())
        self.assertEqual(call.call_count, 1)

    def test_generated_usage_keeps_only_valid_allowlisted_counters(self):
        usage = {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150,
                 "input_tokens_details": {"image_tokens": 100, "text_tokens": 20, "secret": self.key},
                 "output_tokens_details": {"image_tokens": 30, "text_tokens": 0, "metadata": self.key},
                 "secret": self.key}
        response = {"usage": usage, "data": [{"b64_json": base64.b64encode(png('blue')).decode()}]}
        with patch.object(visual, '_edit', return_value=response):
            result = self.create(self.key)
        self.assertEqual(result['status'], 'generated')
        self.assertEqual(result['usage'], {'input_tokens': 120, 'output_tokens': 30, 'total_tokens': 150,
                         'input_tokens_details': {'image_tokens': 100, 'text_tokens': 20},
                         'output_tokens_details': {'image_tokens': 30, 'text_tokens': 0}})
        self.assertNotIn(self.key, str(result))
        usage['input_tokens_details']['image_tokens'] = 999
        self.assertEqual(result['usage']['input_tokens_details']['image_tokens'], 100)

    def test_invalid_usage_counts_are_unknown_and_never_leak_metadata(self):
        for invalid in (True, False, -1, 1.5, '123', None, {}, [], float('nan'), float('inf'), self.key):
            with self.subTest(invalid=invalid):
                usage = {'input_tokens': invalid, 'output_tokens': invalid, 'total_tokens': invalid,
                         'input_tokens_details': {'image_tokens': invalid, 'text_tokens': invalid},
                         'output_tokens_details': {'image_tokens': invalid, 'text_tokens': invalid}, 'secret': self.key}
                with patch.object(visual, '_edit', return_value={'usage': usage, 'data': []}):
                    result = self.create(self.key)
                self.assertIsNone(result['usage'])
                self.assertNotIn(self.key, str(result))
        for malformed in (None, [], 'secret', 42):
            self.assertIsNone(visual._safe_usage(malformed))

    def test_usage_survives_image_validation_and_save_failures(self):
        usage = {'input_tokens': 10, 'output_tokens': 20, 'total_tokens': 30}
        with patch.object(visual, '_edit', return_value={'usage': usage, 'data': []}):
            result = self.create(self.key)
        self.assertEqual(result['errorCode'], 'image_generation_failed')
        self.assertEqual(result['usage'], usage)
        response = {'usage': usage, 'data': [{'b64_json': base64.b64encode(png('blue')).decode()}]}
        with patch.object(visual, '_edit', return_value=response), patch.object(Path, 'mkdir', side_effect=OSError(self.key)):
            result = self.create(self.key)
        self.assertEqual(result['errorCode'], 'image_save_failed')
        self.assertEqual(result['usage'], usage)
        self.assertNotIn(self.key, str(result))
        self.assertFalse(self.output.exists())

    def test_product_swap_retains_original_room_and_changes_lineage(self):
        first = self.create()
        self.product.write_bytes(png("green"))
        self.candidate.update(id="chair-2", exactSku="green-18", sourceImageUrl="/assets/green.png")
        second = self.create()
        self.assertEqual(first["lineage"]["roomSha256"], second["lineage"]["roomSha256"])
        self.assertNotEqual(first["lineage"]["productSha256"], second["lineage"]["productSha256"])
        self.assertEqual(second["lineage"]["candidateId"], "chair-2")
        self.assertEqual(second["lineage"]["exactSku"], "green-18")

    def test_network_timeout_returns_failure_without_retry(self):
        with patch.object(visual, "_edit", side_effect=TimeoutError("timeout")) as call:
            result = self.create(self.key)
        self.assertEqual(result["status"], "failed")
        self.assertFalse(self.output.exists())
        call.assert_called_once()

    def test_malformed_or_unchanged_provider_output_is_not_generated(self):
        responses = [{}, {"data": []}, {"data": [{"b64_json": "not base64"}]},
                     {"data": [{"b64_json": base64.b64encode(b"bad image").decode()}]},
                     {"data": [{"b64_json": base64.b64encode(self.room.read_bytes()).decode()}]}]
        for response in responses:
            with self.subTest(response=response), patch.object(visual, "_edit", return_value=response):
                result = self.create(self.key)
                self.assertEqual(result["status"], "failed")
                self.assertFalse(self.output.exists())

    def test_edit_request_sends_both_exact_inputs_to_fixed_endpoint(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        with patch.object(visual.urllib.request, "urlopen", return_value=response) as call:
            visual._edit((b"room bytes", "image/png"), (b"product bytes", "image/jpeg"), "placement", self.key)
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/images/edits")
        self.assertEqual(request.data.count(b'name="image[]"'), 2)
        self.assertIn(b"room bytes", request.data)
        self.assertIn(b"product bytes", request.data)
        self.assertNotIn(self.key.encode(), request.data)
        self.assertIn(visual.MODEL.encode(), request.data)


if __name__ == "__main__":
    unittest.main()
