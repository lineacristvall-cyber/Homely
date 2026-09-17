# Room workspace visual acceptance — September 17, 2026

Reference: supplied Screenshot 2026-09-17 at12.18.34PM, visually inspected; same design as docs/product-context/mockups/01-mobile-room-voice.png. Desktop guided by10-desktop-project-canvas.png.

Actual browser screenshots of the isolated seeded project on http://127.0.0.1:8768/:
- mobile-390.png:390×844 viewport. All four chips wrap, no horizontal page overflow; lower actions accessible by scrolling.
- mobile-reference-550.png:550×1000, close to width of supplied reference content.
- desktop-1440.png:1440×1000; sidebar/canvas/brief, research action visible at bottom of viewport.
- before-mobile.png and review-*-v1.png are prior captures, not final designs.

Implementation: photo-first mobile Room inside selected project, Homely/project masthead, editorial title, sage icon chips, green idle assistant, Room/Explore/Saved navigation. Desktop keeps sidebar and canvas/brief split; long text clamps with full values in editor. Existing original image and data preserved. No OS status bar or fake browser frame.

Live checks: project selector and return, Edit opening, Keep opening retained notes with explicit unsupported anchoring notice, text composer with microphone-off status, selected-project Explore showing three leads and Saved view. No paid API calls, user project writes, actual microphone recording or external uploads. Main cloud server was not restarted during this visual pass.

23 UI tests passed before final icon/clamp polish; focused mobile regression passed afterward. Final narrow-phone style-chip adjustment was also checked through actual browser geometry and focused regression. Auth stable-click test included in the full suite.

Differences remain intentional: real project photo differs from reference; idle voice has Talk/Type controls rather than fake Listening/waveform/Stop; Keep? is a notes action, not a detected/anchored retained object; unconfirmed measurements remain Unknown. Additional Original/Placement, Change photo and sourcing controls preserve working functions. Explore/Saved visual redesign is outside this Room pass. This is visual acceptance of the selected Room view, not complete product or production acceptance.
