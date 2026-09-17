const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
let browser;
before(async()=>{browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});});
after(async()=>{await browser?.close();});
async function setup(viewport={width:1440,height:1000},options={}) {
 const context=await browser.newContext({viewport});const page=await context.newPage();page.setDefaultTimeout(6000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 if(options.media)await page.addInitScript(({mode})=>{window.trackStops=0;window.mediaRequests=0;Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async()=>{window.mediaRequests++;if(mode==='denied')throw new DOMException('Denied','NotAllowedError');return {getTracks:()=>[{stop:()=>window.trackStops++}]};}},configurable:true});window.MediaRecorder=class {static isTypeSupported(){return true;}constructor(){this.state='inactive';this.mimeType='audio/webm';}start(){this.state='recording';}stop(){this.state='inactive';this.ondataavailable?.({data:new Blob(['mock audio fixture'],{type:'audio/webm'})});setTimeout(()=>this.onstop?.(),0);}};},{mode:options.media});
 let project=null;let authUser=null;const watches=[];const notifications=[];const projectsByUser={};let researchReads=0;let visualIndex=0;let reviewRequests=0;const visualById={};const requests=[];
 const candidates=[{id:'lead-1',title:'Oak dining chair',seller:'Example fixture only',unitPrice:200,shipping:null,tax:null,status:'lead',reason:'Listing only; exact quantity not confirmed',sourceRefs:[],dimensions:{}},{id:'lead-2',title:'Linen dining chair',seller:'Example fixture only',unitPrice:300,shipping:50,tax:100,status:'lead',reason:'Unconfirmed variant',availableQuantity:6,sourceRefs:[],dimensions:{}}];
 const secondProject={id:'p2',name:'Other private room',mode:'pro',version:3,brief:{quantity:6},room:{imageUrl:'/other-room.png',consent:true},candidates:[...candidates],decisions:[]};if(options.savedHistory)project={id:'p1',name:'Saved preview room',mode:'pro',version:3,brief:{quantity:6},room:{imageUrl:'/fixture-room.png',consent:true},candidates:[...candidates],decisions:[]};
 if(options.reviewData&&project){project.brief.notes='PRIVATE DESIGNER NOTES';project.brief.location='PRIVATE LOCATION';project.brief.measurements={tableUndersideIn:27,chairArmIn:26,roomWidthIn:144,roomDepthIn:180};}
 await page.route('**/*',async route=>{const url=new URL(route.request().url());if(url.hostname!=='homely.test')return route.abort();const p=url.pathname;const method=route.request().method();const body=route.request().postDataJSON();if(p.startsWith('/api/')){requests.push({p,method,body});let data={};let status=200;
 if(p==='/api/auth/session')data=options.cloud?{mode:'cloud',authenticated:!!authUser,user:authUser}:{mode:'local',authenticated:false,user:null};
 else if(p==='/api/auth/sign-in'){authUser={id:body.email,email:body.email};project=projectsByUser[authUser.id]||null;data={user:authUser};}
 else if(p==='/api/capabilities')data={passwordRecovery:!!options.authFeatures,confirmationResend:!!options.authFeatures,priceWatch:!!options.watchFeatures};
 else if(p==='/api/auth/recover'||p==='/api/auth/resend')data={requested:true,message:'If this address is eligible, check your email.'};
 else if(p==='/api/auth/reset')data={password_updated:true,sign_in_required:true,message:'Password updated. Sign in with your new password.'};
 else if(p==='/api/watches')data={watches,notifications,delivery:'in_app',schedulerRunning:true,deliveryNote:'Checks run while this server runs. In-app delivery only.'};
 else if(p==='/api/projects/p1/watches'){watches.push({id:'w1',status:'active',product:{title:'Oak dining chair'},lastCheckedAt:1780000000,nextCheckAt:1780003600});notifications.push({id:'n1',title:'Oak dining chair',previousPrice:200,currentPrice:180,createdAt:1780000000,read:false,message:'Observed public-page price changed; stock and delivered total remain unverified.'});data={watch:watches[0]};}
 else if(p==='/api/watches/w1/cancel'){watches[0].status='cancelled';data={watch:watches[0]};}
 else if(p==='/api/notifications/n1/read'){notifications[0].read=true;data={notification:notifications[0]};}
 else if(p==='/api/auth/sign-up')data={email_confirmation_required:true,sign_in_required:true,message:'Check your email to confirm, then sign in.'};
 else if(p==='/api/auth/sign-out'){if(authUser)projectsByUser[authUser.id]=project;authUser=null;project=null;data={signedout:true};}
 else if(p==='/api/privacy/export'){if(options.exportFailure){status=503;data={error:'Fixture export service unavailable'};}else data={schemaVersion:'homely.project-export.v1',exportedAt:'2026-09-13T12:00:00Z',projects:project?[project]:[],exclusions:['image binaries','jobs','audio']};}
 else if(p.endsWith('/fit'))data={gate:{status:options.fitPassed?'passed':'blocked',missing:['Confirmed measurements needed']},candidates:options.fitPassed?candidates.map(c=>({candidateId:c.id,status:options.fitSecondBlocked&&c.id==='lead-2'?'blocked':'passed',checks:[]})):[]};
 else if(p==='/api/health')data={ok:true,openaiConfigured:false};
 else if(p==='/api/projects'&&method==='GET')data={projects:project?[project,...(options.secondProject?[secondProject]:[])]:[]};
 else if(p==='/api/projects'&&method==='POST'){project={id:'p1',name:body.name,mode:body.mode,version:1,brief:{itemType:'Dining chairs',quantity:6},room:null,candidates:[],decisions:[]};data={project};}
 else if(p==='/api/projects/p1/assistant'){if(body.confirmationId){project.brief.quantity=4;project.version++;data={reply:'Quantity updated to four in your saved brief.',project};}else if(body.message==='Set quantity to four'){data={reply:'I can update the quantity. Please review first.',confirmation:{id:'confirm-quantity',summary:'Change chair quantity from six to four.'}};}else if(body.message==='Compare the first two'){project.candidates=candidates;data={reply:'Comparing the two current research leads.',project,command:{type:'compare_candidates',candidateIds:['lead-1','lead-2','not-in-project']}};}else if(body.message==='Show oak only'){project.candidates=candidates;data={reply:'Showing the selected oak lead.',project,command:{type:'filter_candidates',candidateIds:['lead-1']}};}else data={reply:'Your message was received against the saved project context.'};}
 else if(p==='/api/transcriptions'){if(options.transcriptionDelayMs)await new Promise(r=>setTimeout(r,options.transcriptionDelayMs));data={text:'Set quantity to four'};}
 else if(p==='/api/projects/p1/review-preview'){reviewRequests++;if(options.reviewConflict&&reviewRequests===1){project.version++;status=409;data={error:'Project version changed'};}else {const selection=body.scope;data={canCreateReview:false,preview:{schemaVersion:'homely.review-preview.v1',projectVersion:project.version,disclosure:selection,candidates:project.candidates.filter(c=>selection.candidateIds.includes(c.id)).map(c=>({id:c.id,title:c.title,seller:c.seller,exactSku:null,variant:null,availability:{sourceStatus:c.status,currentStatus:'unverified',observedAt:null,availableQuantity:null},cost:{unitPrice:c.unitPrice,shipping:c.shipping,tax:c.tax,deliveredTotal:null},dimensions:c.dimensions,fitStatus:'unverified'})),notes:selection.noteFields.includes('notes')?{notes:project.brief.notes}:{},measurements:Object.fromEntries(selection.measurementFields.map(key=>[key,project.brief.measurements[key]])),images:[],limitations:['Owner-only; no recipient access exists.','Quantity and budget limits are not included.'],disclosureHash:'fixture-disclosure-hash'}};}}
 else if(p==='/api/projects/p1/room'){project.room={imageUrl:'/fixture-room.png',consent:body.consent};project.version++;data={project};}
 else if((p==='/api/projects/p1/visualizations'||p==='/api/projects/p2/visualizations')&&method==='GET'){if(options.historyDelayMs)await new Promise(r=>setTimeout(r,options.historyDelayMs));const jobs=options.savedHistory&&p.includes('/p1/')?[{id:'saved-v1',projectId:'p1',projectVersion:options.staleHistory?2:3,kind:'visualization',candidateId:'lead-1',createdAt:'2026-09-13T12:00:00Z',status:options.staleHistory?'cancelled':'completed',result:{imageUrl:'/saved-render.png',stale:!!options.staleHistory,illustrative:true,identityStatus:'unverified',fitStatus:'unknown',fitReason:'Room measurements missing.',roomImageUrl:'/fixture-room.png',sourceImageUrl:'/saved-product.png',lineage:{candidateId:'lead-1'}}}]:[];data={jobs};}
 else if(p==='/api/projects/p1/visualizations'&&method==='POST'){const id='v'+(++visualIndex);visualById[id]=body.candidateId;data={job:{id,status:'queued'}};}
 else if(/^\/api\/jobs\/v[0-9]+$/.test(p)){const id=p.split('/').at(-1);if(options.visualSuccess){await new Promise(r=>setTimeout(r,options.visualDelayMs||100));data={job:{id,status:'completed',result:{imageUrl:'/fixture-render-'+visualById[id]+'.png',illustrative:true,identityStatus:'unverified',fitStatus:'unknown',fitReason:'Table underside measurement missing.',roomImageUrl:'/fixture-room.png',sourceImageUrl:'/fixture-product-'+visualById[id]+'.png'}}};}else data={job:{id,status:'failed',error:'Synthetic fixture: no live image provider'}};}
 else if(p==='/api/projects/p1/brief'){project.brief={...project.brief,...body.brief,measurements:{...project.brief.measurements,...body.brief.measurements}};project.version++;data={project};}
 else if(p==='/api/projects/p1/product-urls'){project.candidates.push({...candidates[0],id:'import-1'});data={candidate:project.candidates.at(-1),project};}
 else if(p==='/api/projects/p1/research'){data={job:{id:'j1',status:'queued'}};}
 else if(p==='/api/jobs/j1/cancel'){if(options.cancelScenario==='already_completed'){project.candidates=candidates;data={job:{id:'j1',status:'completed',progress:'Research complete'}};}else if(options.cancelScenario==='failed'){status=503;data={error:'Fixture cancellation unavailable'};}else data={job:{id:'j1',status:'cancelled',progress:'Cancelled; no late results will replace your project'}};}
 else if(p==='/api/jobs/j1'){researchReads++;if(options.partialCoverage){data={job:{id:'j1',status:'failed',error:'Fixture source failure.',result:{sourceCoverageComplete:false,sourceCoverage:[{url:'https://provider.example.invalid/discovery',sourceId:'fixture.discovery',stage:'discovery',status:'completed',observedAt:'2026-09-13T12:00:00Z',reason:'Provider discovery completed; internal sites unavailable.'},{url:'https://blocked.example.invalid/chair',sourceId:'fixture.blocked',stage:'enrichment',status:'blocked',observedAt:'2026-09-13T12:00:01Z',reason:'Robots rules blocked this public-page attempt.'},{url:'https://timeout.example.invalid/chair',sourceId:'fixture.timeout',stage:'enrichment',status:'failed',observedAt:'2026-09-13T12:00:02Z',reason:'Page timed out; lead retained.'}]}}};}else if(options.cancelScenario){if(researchReads===1)data={job:{id:'j1',status:'running',progress:'Checking fixture sources'}};else {await new Promise(r=>setTimeout(r,500));data={job:{id:'j1',status:options.cancelScenario==='failed'?'running':'completed',progress:'Delayed fixture response'}};}}else {project.candidates=candidates;data={job:{id:'j1',status:'completed'}};}}
 else if(p==='/api/projects/p1/decisions'){project.decisions.push({candidateId:body.candidateId,createdAt:new Date().toISOString(),deliveredTotal:null});data={decision:project.decisions.at(-1)};}
 else if(p==='/api/projects/p1/handoff')data={status:'blocked',reason:'Exact variant and quantity are not verified.'};
 else if(p==='/api/projects/p2')data={project:secondProject};
 else if(p==='/api/projects/p1')data={project};
 else {status=404;data={error:'Unknown mock endpoint '+p};}
 return route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
 }
 const file=p==='/'?'index.html':p.slice(1);try{return route.fulfill({contentType:file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':'text/html',body:await fs.readFile(path.join(__dirname,'..',file))});}catch{return route.abort();}
 });await page.goto('http://homely.test');return {page,context,requests,errors};
}
async function openDetails(page){if(!await page.locator('#project-details').evaluate(el=>el.open))await page.locator('#project-details > summary').click();}
async function createRoom(page,name){await page.getByRole('button',{name:'Other room',exact:true}).click();await page.getByLabel('Room name',{exact:true}).fill(name);await page.getByRole('button',{name:'Continue',exact:true}).click();await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();await openDetails(page);}
async function openBrief(page){await openDetails(page);if(!await page.locator('#brief-editor').evaluate(el=>el.open))await page.getByRole('button',{name:'Edit brief',exact:true}).click();}
test('desktop: create, budget validation, research leads, comparison, evidence, decision and blocked handoff',async()=>{
 const {page,context,requests,errors}=await setup();
 await createRoom(page,'Dining room test');
 await page.getByRole('heading',{name:'Dining room test',exact:true}).waitFor();
 await openBrief(page);await page.getByLabel('Flexible target ($)').fill('3000');await page.getByLabel('Hard cap ($)').fill('2000');
 await page.getByRole('button',{name:'Save brief'}).click();
 await page.getByRole('status').filter({hasText:'flexible target is above'}).waitFor();
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).length,1,'invalid budget must not add a save');
 await openBrief(page);await page.getByLabel('Flexible target ($)').fill('1500');
 if(!await page.getByRole('button',{name:'Find pieces for this room'}).isVisible())await page.locator('.room-research-actions > summary').click();await page.getByRole('button',{name:'Find pieces for this room'}).click();
 await page.getByRole('heading',{name:'Oak dining chair'}).waitFor();
 assert.equal(await page.getByText('Research lead · unconfirmed',{exact:true}).count(),2);
 assert.equal(await page.getByRole('heading',{name:'Ready recommendations',exact:true}).count(),0);
 await page.getByLabel('Add to comparison').nth(0).check();await page.getByLabel('Add to comparison').nth(1).check();
 await page.getByRole('button',{name:'Compare (2)',exact:true}).click();
 await page.getByRole('heading',{name:'Compare your possibilities.'}).waitFor();
 assert.match(await page.locator('.compare-table').innerText(),/Unknown/);
 await page.getByRole('button',{name:'Close',exact:true}).click();
 await page.getByRole('button',{name:'Source coverage',exact:true}).click();await page.getByRole('heading',{name:'A view of where we looked.'}).waitFor();assert.match(await page.locator('#detail-content').innerText(),/Partial source coverage/);await page.getByRole('button',{name:'Close',exact:true}).click();
 await page.getByRole('button',{name:'View evidence'}).first().click();assert.equal(await page.locator('#detail-dialog').evaluate(d=>d.scrollTop),0);
 await page.getByRole('button',{name:'Save decision'}).click();
 await page.locator('.mobile-nav [data-view=saved]').click();
 await page.getByRole('button',{name:'Recheck & hand off'}).click();
 await page.getByRole('status').filter({hasText:'Exact variant and quantity are not verified'}).waitFor();
 assert.equal(await page.getByRole('link',{name:'Continue to seller'}).count(),0);
 assert.deepEqual(errors,[]);await context.close();
});
test('mobile: responsive initial screen, project creation, room consent and keyboard dialog dismissal',async()=>{
 const {page,context,errors}=await setup({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'no horizontal overflow');
 await createRoom(page,'Mobile studio');
 await page.getByRole('button',{name:'Add your room photo'}).click();
 await page.getByLabel('I have permission to use this photo').waitFor();
 assert.equal(await page.getByLabel('I have permission to use this photo').isChecked(),false);
 await page.keyboard.press('Escape');assert.equal(await page.locator('#detail-dialog').evaluate(d=>d.open),false);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});

test('unsaved brief survives navigation, unavailable affordances, and reload without claiming saved',async()=>{
 const {page,context,requests,errors}=await setup();
 await createRoom(page,'Draft preservation');
 await page.getByRole('heading',{name:'Draft preservation',exact:true}).waitFor();await openBrief(page);await page.getByLabel('Location',{exact:true}).fill('Oakland, CA');await page.getByLabel('The feeling you’re after').fill('Warm, but not matchy. Keep my oak table.');
 assert.deepEqual(errors,[]);await page.getByText('Unsaved changes · draft kept in this browser tab',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Choose project',exact:true}).click();await page.getByRole('button',{name:/Partly available Camera & room capture/}).click();await page.locator('#feature-content').getByRole('heading',{name:'Camera & room capture'}).waitFor();await page.getByRole('button',{name:'Back to my project'}).click();await page.getByRole('button',{name:/Draft preservation ↗/}).click();
 assert.equal(await page.getByLabel('Location',{exact:true}).inputValue(),'Oakland, CA');
 await page.locator('.mobile-nav [data-view="findings"]').click();await page.locator('.mobile-nav [data-view=workspace]').click();
 assert.equal(await page.getByLabel('The feeling you’re after').inputValue(),'Warm, but not matchy. Keep my oak table.');
 await page.reload();await page.getByLabel('Location',{exact:true}).waitFor();
 assert.equal(await page.getByLabel('Location',{exact:true}).inputValue(),'Oakland, CA');
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).length,1);
 await page.getByRole('button',{name:'Save brief'}).click();await page.getByText('Saved brief · local project',{exact:true}).waitFor({state:'attached'});
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).length,2);await context.close();
});

test('mobile project chooser and URL import remain accessible without claiming stock',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844});
 await createRoom(page,'Mobile project chooser');await page.getByRole('heading',{name:'Mobile project chooser',exact:true}).waitFor();
 await page.getByRole('button',{name:'Edit brief'}).click();assert.ok(await page.getByLabel('What are we looking for?').evaluate(el=>el.getBoundingClientRect().top)<844);
 await page.locator('.mobile-nav [data-view="more"]').click();await page.getByRole('heading',{name:'Your projects',exact:true}).waitFor();
 await page.locator('.mobile-project-list button').click();await openBrief(page);await page.locator('.room-research-actions > summary').waitFor();
 await page.locator('.mobile-nav [data-view="findings"]').click();await page.getByLabel('Product page URL').fill('https://shop.example.com/product');await page.getByRole('button',{name:'Import a lead'}).click();
 await page.getByRole('heading',{name:'Oak dining chair'}).waitFor();assert.equal(requests.filter(r=>r.p.endsWith('/product-urls')).length,1);
 assert.equal(await page.getByText('Research lead · unconfirmed',{exact:true}).count(),1);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});

async function assistantProject(page){await createRoom(page,'Conversation test');await page.getByRole('heading',{name:'Conversation test',exact:true}).waitFor();await openBrief(page);}
async function sendMessage(page,text){await page.getByLabel('Your message / editable transcript').fill(text);await page.getByRole('button',{name:'Send to Homely'}).click();}
test('typed assistant proposes, cancels, confirms against version, then opens real comparison and filters',async()=>{
 const {page,context,requests,errors}=await setup();await assistantProject(page);
 await sendMessage(page,'Set quantity to four');await page.getByText('Proposed change · not applied',{exact:true}).waitFor();assert.equal(requests.filter(r=>r.body?.confirmationId).length,0);
 await page.getByRole('button',{name:'Cancel proposal'}).click();assert.equal(requests.filter(r=>r.body?.confirmationId).length,0);
 await sendMessage(page,'Set quantity to four');await page.getByRole('button',{name:'Confirm this change'}).click();await page.getByText('Quantity updated to four in your saved brief.',{exact:true}).waitFor();
 assert.equal(await page.getByLabel('How many?').inputValue(),'4');assert.deepEqual(requests.find(r=>r.body?.confirmationId).body,{confirmationId:'confirm-quantity',expectedVersion:2});
 await sendMessage(page,'Compare the first two');await page.getByRole('heading',{name:'Compare your possibilities.'}).waitFor();assert.equal(await page.locator('.compare-table thead th').count(),3);await page.getByRole('button',{name:'Close',exact:true}).click();
 await sendMessage(page,'Show oak only');await page.getByRole('button',{name:'Show all findings'}).waitFor();assert.equal(await page.locator('.candidate').count(),1);await page.getByRole('button',{name:'Show all findings'}).click();assert.equal(await page.locator('.candidate').count(),2);assert.deepEqual(errors,[]);await context.close();
});
test('voice permission denied keeps typed fallback; consent required before microphone request',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844},{media:'denied'});await assistantProject(page);
 await page.getByLabel('Your message / editable transcript').fill('Keep this draft');await page.getByRole('button',{name:'Talk to Homely'}).click();await page.getByRole('button',{name:'Start recording'}).click();assert.equal(await page.evaluate(()=>window.mediaRequests),0);
 await page.getByLabel('I consent to recording and sending this audio').check();await page.getByRole('button',{name:'Start recording'}).click();await page.getByRole('alert').filter({hasText:'Microphone permission was denied'}).waitFor();
 assert.equal(await page.getByLabel('Your message / editable transcript').inputValue(),'Keep this draft');await page.getByRole('button',{name:'Send to Homely'}).click();await page.getByText('Your message was received against the saved project context.',{exact:true}).waitFor();assert.equal(requests.filter(r=>r.p==='/api/transcriptions').length,0);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});
test('voice stop creates editable transcript only; cancel releases tracks and discards stale transcription',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{media:'fake',transcriptionDelayMs:350});await assistantProject(page);
 const start=async()=>{await page.getByRole('button',{name:'Talk to Homely'}).click();await page.getByLabel('I consent to recording and sending this audio').check();await page.getByRole('button',{name:'Start recording'}).click();await page.getByRole('button',{name:'Stop & review transcript'}).waitFor();};
 await start();await page.getByRole('button',{name:'Cancel recording'}).click();assert.ok(await page.evaluate(()=>window.trackStops)>0);assert.equal(requests.filter(r=>r.p==='/api/transcriptions').length,0);
 await start();await page.getByRole('button',{name:'Stop & review transcript'}).click();await page.getByText('Transcript ready. Correct it above, then choose Send.',{exact:true}).waitFor();assert.equal(await page.getByLabel('Your message / editable transcript').inputValue(),'Set quantity to four');assert.equal(requests.filter(r=>r.p.endsWith('/assistant')).length,0);
 await page.getByLabel('Your message / editable transcript').fill('My corrected draft');await start();await page.getByRole('button',{name:'Stop & review transcript'}).click();await page.getByRole('button',{name:'Cancel voice input'}).click();await page.waitForTimeout(500);assert.equal(await page.getByLabel('Your message / editable transcript').inputValue(),'My corrected draft');
 assert.equal(requests.filter(r=>r.p.endsWith('/assistant')).length,0);assert.deepEqual(errors,[]);await context.close();
});

test('cloud auth gates project reads; sign-up and sign-out separate account drafts, conversation, and passwords',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{cloud:true});
 await page.getByRole('heading',{name:'Welcome back'}).waitFor();assert.equal(requests.filter(r=>r.p==='/api/projects').length,0);
 await page.getByLabel('Email',{exact:true}).fill('qa-a@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fixture-password-only');await page.getByRole('button',{name:'Create account',exact:true}).click();await page.getByText('Check your email to confirm, then sign in.',{exact:true}).waitFor();assert.equal(requests.filter(r=>r.p==='/api/projects').length,0);
 const signIn=async(email)=>{await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill('fixture-password-only');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.locator('#auth-account').waitFor({state:'attached'});await page.locator('#auth-form').waitFor({state:'detached'});};
 const signOut=async()=>{if(!await page.locator('#auth-account').isVisible())await page.getByRole('button',{name:'Projects and account menu',exact:true}).click();await page.locator('#auth-account').click();await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByRole('heading',{name:'Welcome back'}).waitFor();};
 await signIn('qa-a@example.invalid');await assistantProject(page);assert.equal(await page.locator('#workspace-mode').innerText(),'Private cloud workspace');await openBrief(page);await page.getByText('Saved brief · private cloud project',{exact:true}).waitFor();await page.getByLabel('Location',{exact:true}).fill('Account A draft only');await sendMessage(page,'Account A private conversation');await page.getByText('Your message was received against the saved project context.',{exact:true}).waitFor();await signOut();
 assert.doesNotMatch(await page.locator('body').innerText(),/Account A private conversation/);await signIn('qa-b@example.invalid');await assistantProject(page);assert.equal(await page.getByLabel('Location',{exact:true}).inputValue(),'');assert.doesNotMatch(await page.locator('#assistant-messages').innerText(),/Account A private conversation/);await openBrief(page);await page.getByLabel('Location',{exact:true}).fill('Account B separate draft');await signOut();
 await signIn('qa-a@example.invalid');await page.getByLabel('Location',{exact:true}).waitFor();assert.equal(await page.getByLabel('Location',{exact:true}).inputValue(),'Account A draft only');await page.locator('#assistant-message').focus();await page.getByText('Account A private conversation',{exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>JSON.stringify({...sessionStorage,...localStorage}).includes('fixture-password-only')),false);assert.deepEqual(errors,[]);await context.close();
});

test('room and visualization image requests carry the captured project version and explicit consent',async()=>{
 const {page,context,requests,errors}=await setup();await assistantProject(page);
 const image={name:'fixture.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jY1cAAAAASUVORK5CYII=','base64')};
 await page.getByRole('button',{name:'Add your room photo'}).click();await page.getByLabel('Room photo',{exact:true}).setInputFiles(image);await page.getByLabel('I have permission to use this photo').check();await page.getByRole('button',{name:'Save room photo'}).click();await page.getByText('Room photo saved. Your original is preserved.',{exact:true}).waitFor();
 const upload=requests.find(r=>r.p.endsWith('/room'));assert.equal(upload.body.expectedVersion,2);assert.equal(upload.body.consent,true);
 if(!await page.getByRole('button',{name:'Find pieces for this room'}).isVisible())await page.locator('.room-research-actions > summary').click();await page.getByRole('button',{name:'Find pieces for this room'}).click();await page.getByRole('heading',{name:'Oak dining chair'}).waitFor();await page.getByRole('button',{name:'In your room',exact:true}).first().click();
 await page.getByLabel('Exact product source image').setInputFiles(image);await page.getByLabel('This reference shows the selected product and variant').check();await page.getByLabel('I confirm this is the selected product variant').check();await page.getByRole('button',{name:'Create illustrative preview'}).click();await page.getByText('Synthetic fixture: no live image provider',{exact:true}).first().waitFor();
 const visual=requests.find(r=>r.p.endsWith('/visualizations')&&r.method==='POST');assert.equal(visual.body.expectedVersion,4);assert.equal(visual.body.productImageRightsConfirmed,true);assert.equal(visual.body.candidateId,'lead-1');assert.deepEqual(errors,[]);await context.close();
});

test('cancel research preserves cancelled state when an older completed poll arrives late',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{cancelScenario:'late_completed'});await assistantProject(page);if(!await page.getByRole('button',{name:'Find pieces for this room'}).isVisible())await page.locator('.room-research-actions > summary').click();await page.getByRole('button',{name:'Find pieces for this room'}).click();await page.getByText('Checking fixture sources',{exact:false}).waitFor();
 await page.waitForRequest(r=>new URL(r.url()).pathname==='/api/jobs/j1');await page.getByRole('button',{name:'Cancel research',exact:true}).click();await page.getByRole('heading',{name:'Research cancelled',exact:true}).waitFor();await page.waitForTimeout(650);
 assert.equal(await page.getByRole('heading',{name:'Research cancelled',exact:true}).count(),1);assert.equal(await page.getByRole('button',{name:'Cancel research',exact:true}).isDisabled(),true);assert.equal(requests.filter(r=>r.p==='/api/jobs/j1/cancel').length,1);assert.equal(requests.filter(r=>r.p==='/api/projects/p1'&&r.method==='GET').length,0);assert.equal(await page.getByRole('heading',{name:'Research is ready to explore'}).count(),0);assert.deepEqual(errors,[]);await context.close();
});
test('cancel displays server-completed result honestly instead of claiming cancellation',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{cancelScenario:'already_completed'});await assistantProject(page);if(!await page.getByRole('button',{name:'Find pieces for this room'}).isVisible())await page.locator('.room-research-actions > summary').click();await page.getByRole('button',{name:'Find pieces for this room'}).click();await page.getByRole('button',{name:'Cancel research',exact:true}).click();await page.getByText('Research finished before cancellation. Its saved findings are available.',{exact:true}).waitFor();
 await page.getByRole('heading',{name:'Oak dining chair'}).waitFor();assert.equal(await page.getByRole('heading',{name:'Research cancelled',exact:true}).count(),0);assert.equal(requests.filter(r=>r.p==='/api/jobs/j1/cancel').length,1);assert.deepEqual(errors,[]);await context.close();
});

test('failed research displays actual partial source attempts without inferring internet coverage',async()=>{
 const {page,context,errors}=await setup({width:390,height:844},{partialCoverage:true});await assistantProject(page);await page.locator('.room-research-actions > summary').click();if(!await page.getByRole('button',{name:'Find pieces for this room'}).isVisible())await page.locator('.room-research-actions > summary').click();await page.getByRole('button',{name:'Find pieces for this room'}).click();await page.getByRole('heading',{name:'Research needs another try'}).waitFor();await page.getByRole('button',{name:'Review source attempts',exact:true}).click();
 assert.equal(await page.locator('.source-ledger>li').count(),3);await page.getByText('1 completed',{exact:true}).waitFor();await page.getByText('1 blocked',{exact:true}).waitFor();await page.getByText('1 failed',{exact:true}).waitFor();await page.getByText('Robots rules blocked this public-page attempt.',{exact:true}).waitFor();
 assert.match(await page.locator('#detail-content').innerText(),/Latest research job/);assert.match(await page.locator('#detail-content').innerText(),/provider’s internal attempted sites are unavailable/);assert.equal(await page.locator('.source-ledger a').count(),3);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});

test('visualization requires reference match and rights; pending job prevents duplicates and result stays with its candidate',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{visualSuccess:true,visualDelayMs:900});await assistantProject(page);
 const image={name:'fixture.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jY1cAAAAASUVORK5CYII=','base64')};
 await page.getByRole('button',{name:'Add your room photo'}).click();await page.getByLabel('Room photo',{exact:true}).setInputFiles(image);await page.getByLabel('I have permission to use this photo').check();await page.getByRole('button',{name:'Save room photo'}).click();await page.getByText('Room photo saved. Your original is preserved.',{exact:true}).waitFor();if(!await page.getByRole('button',{name:'Find pieces for this room'}).isVisible())await page.locator('.room-research-actions > summary').click();await page.getByRole('button',{name:'Find pieces for this room'}).click();await page.getByRole('heading',{name:'Oak dining chair'}).waitFor();
 await page.getByRole('button',{name:'In your room',exact:true}).first().click();await page.getByLabel('Exact product source image').setInputFiles(image);await page.getByAltText('Selected source reference for Oak dining chair').waitFor();await page.getByRole('button',{name:'Create illustrative preview'}).click();assert.equal(requests.filter(r=>r.p.endsWith('/visualizations')&&r.method==='POST').length,0);
 await page.getByLabel('This reference shows the selected product and variant').check();await page.getByRole('button',{name:'Create illustrative preview'}).click();assert.equal(requests.filter(r=>r.p.endsWith('/visualizations')&&r.method==='POST').length,0);await page.getByLabel('I confirm this is the selected product variant').check();await page.getByRole('button',{name:'Create illustrative preview'}).click();await page.getByText('Visualization queued',{exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:'Create illustrative preview'}).isDisabled(),true);
 await page.getByRole('button',{name:'Close',exact:true}).click();await page.getByRole('button',{name:'In your room',exact:true}).nth(1).click();await page.waitForTimeout(1100);assert.equal(await page.getByAltText('Illustrative generated product-in-room preview').count(),0);await page.getByRole('button',{name:'Close',exact:true}).click();await page.getByRole('button',{name:'In your room',exact:true}).first().click();
 await page.getByAltText('Illustrative generated product-in-room preview').waitFor();assert.match(await page.locator('#visual-result').innerText(),/Product identity: unverified/);assert.match(await page.locator('#visual-result').innerText(),/Physical fit: unknown/);await page.getByText('Table underside measurement missing.',{exact:false}).waitFor();assert.equal(await page.getByRole('link',{name:'Product source image',exact:true}).count(),1);assert.equal(requests.filter(r=>r.p.endsWith('/visualizations')&&r.method==='POST').length,1);assert.deepEqual(errors,[]);await context.close();
});

test('project JSON export downloads the real response and clearly excludes a complete backup',async()=>{
 const {page,context,requests,errors}=await setup();await assistantProject(page);await page.getByRole('button',{name:'Projects and account menu',exact:true}).click();await page.getByRole('button',{name:'Settings & privacy'}).click();await page.getByText('This is a project-data export, not a complete account or image backup.',{exact:false}).waitFor();
 const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Download project JSON'}).click();const download=await downloading;assert.equal(download.suggestedFilename(),'homely-project-export.json');const stream=await download.createReadStream();const chunks=[];for await(const chunk of stream)chunks.push(chunk);const data=JSON.parse(Buffer.concat(chunks).toString());assert.equal(data.schemaVersion,'homely.project-export.v1');assert.equal(data.projects[0].name,'Conversation test');
 await page.getByText('Project JSON download started. Image files, jobs, and audio are not included.',{exact:true}).waitFor();assert.equal(requests.filter(r=>r.p==='/api/privacy/export').length,1);assert.equal(requests.filter(r=>r.method==='DELETE').length,0);assert.deepEqual(errors,[]);await context.close();
});
test('mobile export failure remains visible, retryable, and never claims download success',async()=>{
 const {page,context,errors}=await setup({width:390,height:844},{exportFailure:true});await assistantProject(page);await page.locator('.mobile-nav [data-view="more"]').click();await page.getByRole('button',{name:'Download project JSON'}).click();await page.getByText('Export failed: Fixture export service unavailable',{exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:'Download project JSON'}).isDisabled(),false);assert.equal(await page.getByText('Project JSON download started.',{exact:false}).count(),0);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});

test('saved current preview reloads from history and Placement toggles without generating',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true});await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();await openDetails(page);if(!await page.locator('[data-placement]').isVisible())await page.locator('.room-photo-options > summary').click();await page.locator('[data-placement]').click();await page.getByAltText('Illustrative placement of Oak dining chair').waitFor();assert.match(await page.locator('.placement-caption').innerText(),/Product identity: unverified/);assert.match(await page.locator('.placement-caption').innerText(),/Physical fit: unknown/);
 if(!await page.locator('[data-original]').isVisible())await page.locator('.room-photo-options > summary').click();await page.locator('[data-original]').click();await page.locator('.room-canvas').getByAltText('Your original room',{exact:true}).waitFor();assert.equal(await page.getByAltText('Illustrative placement of Oak dining chair').count(),0);await page.reload();await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();await openDetails(page);if(!await page.locator('[data-placement]').isVisible())await page.locator('.room-photo-options > summary').click();await page.locator('[data-placement]').click();await page.getByAltText('Illustrative placement of Oak dining chair').waitFor();await page.getByRole('button',{name:'View source & fit details'}).click();await page.getByAltText('Illustrative generated product-in-room preview').waitFor();
 assert.equal(requests.filter(r=>r.method==='POST').length,0);assert.ok(requests.filter(r=>r.p==='/api/projects/p1/visualizations'&&r.method==='GET').length>=2);assert.deepEqual(errors,[]);await context.close();
});
test('stale saved preview is withheld with explanation and no silent regenerate',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844},{savedHistory:true,staleHistory:true});await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();await openDetails(page);if(!await page.locator('[data-placement]').isVisible())await page.locator('.room-photo-options > summary').click();await page.locator('[data-placement]').click();await page.getByText('Saved previews belong to an earlier project version or are no longer current. The original room remains visible.',{exact:true}).waitFor();
 assert.equal(await page.getByAltText('Illustrative placement of Oak dining chair').count(),0);assert.equal(requests.filter(r=>r.method==='POST').length,0);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});
test('delayed preview history from a previous project cannot appear after switching projects',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true,secondProject:true,historyDelayMs:700});await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();await page.getByRole('button',{name:'Choose project',exact:true}).click();await page.locator('.mobile-project-list [data-project="p2"]').click();await page.getByRole('heading',{name:'Other private room',exact:true}).waitFor();await openDetails(page);if(!await page.locator('[data-placement]').isVisible())await page.locator('.room-photo-options > summary').click();await page.locator('[data-placement]').click();await page.waitForTimeout(950);
 assert.equal(await page.getByAltText('Illustrative placement of Oak dining chair').count(),0);assert.equal(await page.locator('.room-canvas img').getAttribute('src'),'http://homely.test/other-room.png');await page.getByText('There is no saved current preview for this room yet.',{exact:false}).waitFor();assert.equal(requests.filter(r=>r.method==='POST').length,0);assert.deepEqual(errors,[]);await context.close();
});

test('owner-only disclosure defaults empty and returns only explicitly selected candidate and measurement',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true,reviewData:true});await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();await page.getByRole('button',{name:'Projects and account menu',exact:true}).click();await page.locator('.rail [data-view="review"]').click();assert.equal(await page.locator('#review-scope-form input:checked').count(),0);assert.equal(await page.getByLabel('Room and product images — not available yet').isDisabled(),true);
 await page.getByRole('button',{name:'Preview selected disclosure'}).click();await page.getByRole('heading',{name:'Your selected disclosure.'}).waitFor();let output=await page.locator('.review-output').innerText();assert.doesNotMatch(output,/PRIVATE DESIGNER NOTES|PRIVATE LOCATION|Oak dining chair|roomDepthIn/);assert.deepEqual(requests.find(r=>r.p.endsWith('/review-preview')).body.scope,{candidateIds:[],noteFields:[],measurementFields:[],imageIds:[]});
 await page.getByLabel('Oak dining chair',{exact:true}).check();await page.getByLabel('Table underside height',{exact:true}).check();await page.getByRole('button',{name:'Preview selected disclosure'}).click();await page.getByRole('heading',{name:'Your selected disclosure.'}).waitFor();output=await page.locator('.review-output').innerText();assert.match(output,/Oak dining chair/);assert.match(output,/Table underside height/);assert.match(output,/27 in/);assert.doesNotMatch(output,/Linen dining chair|PRIVATE DESIGNER NOTES|PRIVATE LOCATION|roomDepthIn|chairArmIn/);assert.match(output,/unverified/);assert.doesNotMatch(output,/candidateIds|measurementFields|schemaVersion|homely.review-preview/);
 const submitted=requests.filter(r=>r.p.endsWith('/review-preview')).at(-1).body;assert.deepEqual(submitted,{expectedVersion:3,scope:{candidateIds:['lead-1'],noteFields:[],measurementFields:['tableUndersideIn'],imageIds:[]}});assert.equal(requests.filter(r=>/share|recipient|invite/.test(r.p)).length,0);assert.equal(await page.locator('#view').getByRole('button',{name:/Send|Approve|Create client link/}).count(),0);assert.deepEqual(errors,[]);await context.close();
});
test('stale disclosure preview errors safely and requires reload plus explicit preview again',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844},{savedHistory:true,reviewData:true,reviewConflict:true});await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();await page.locator('.mobile-nav [data-view="more"]').click();await page.locator('[data-feature="share"]').click();await page.getByLabel('Include saved brief notes').check();await page.getByRole('button',{name:'Preview selected disclosure'}).click();await page.getByRole('alert').filter({hasText:'The project changed.'}).waitFor();assert.doesNotMatch(await page.locator('.review-output').innerText(),/PRIVATE DESIGNER NOTES/);
 await page.getByRole('button',{name:'Reload latest project'}).click();await page.getByRole('button',{name:'Preview selected disclosure'}).click();await page.getByRole('heading',{name:'Your selected disclosure.'}).waitFor();assert.match(await page.locator('.review-output').innerText(),/PRIVATE DESIGNER NOTES/);assert.doesNotMatch(await page.locator('.review-output').innerText(),/PRIVATE LOCATION/);assert.equal(requests.filter(r=>r.p.endsWith('/review-preview')).at(-1).body.expectedVersion,4);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});


test('room workspace shows compact truthful summary and explicit editor preserves drafts',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true});
 await page.getByRole('heading',{name:'Saved preview room',exact:true}).waitFor();
 assert.equal(await page.locator('#brief-editor').evaluate(el=>el.open),false);
 assert.match(await page.locator('.measurement-summary').textContent(),/Room width[\s\S]*Unknown/);
 assert.equal(await page.locator('#assistant-panel').isVisible(),true);
 await openDetails(page);assert.equal(await page.locator('.setup-hero').count(),0);const choices=await page.locator('.furnishing-choices').boundingBox();assert.ok(choices.width>300);assert.ok(choices.y<350);
 await openBrief(page);await page.getByLabel('The feeling you’re after').fill('Warm with blue accents');
 assert.match(await page.locator('#brief-summary').textContent(),/Warm with blue accents/);
 await page.locator('.mobile-nav [data-view="findings"]').click();await page.locator('.mobile-nav [data-view="workspace"]').click();
 assert.equal(await page.getByLabel('The feeling you’re after').inputValue(),'Warm with blue accents');
 assert.match(await page.locator('#brief-save-status').innerText(),/Unsaved changes/);
 await page.getByRole('button',{name:'Save brief'}).click();await page.getByText('Saved brief · local project',{exact:true}).waitFor({state:'attached'});
 assert.equal(await page.locator('#brief-editor').evaluate(el=>el.open),false);assert.match(await page.locator('#brief-summary').textContent(),/Warm with blue accents/);
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).length,1);assert.deepEqual(errors,[]);await context.close();
});

 test('cloud sign-in fields survive clicks and session renders in the focused auth shell',async()=>{
 const {page,context}=await setup(undefined,{cloud:true});
 await page.getByLabel('Email',{exact:true}).fill('fixture@example.test');
 await page.getByLabel('Password',{exact:true}).click();
 await page.getByLabel('Password',{exact:true}).fill('synthetic-only');
 await page.getByLabel('Email',{exact:true}).click();
 assert.equal(await page.getByLabel('Email',{exact:true}).inputValue(),'fixture@example.test');
 assert.equal(await page.getByLabel('Password',{exact:true}).inputValue(),'synthetic-only');
 assert.equal(await page.locator('.rail').isVisible(),false);assert.ok((await page.locator('.journey-auth').boundingBox()).y<180);await page.evaluate(()=>render());assert.equal(await page.getByLabel('Email',{exact:true}).evaluate(el=>document.activeElement===el),true);
 assert.equal(await page.getByLabel('Password',{exact:true}).inputValue(),'synthetic-only');
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await page.getByRole('button',{name:'Dining room',exact:true}).waitFor();
 assert.equal(await page.locator('#auth-form').count(),0);
 await context.close();
 });

test('mobile room uses original photo, exposes all constraints and keeps voice idle until requested',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844},{savedHistory:true});
 await openDetails(page);await page.locator('.room-canvas img').waitFor();
 assert.equal(await page.locator('.room-canvas img').getAttribute('src'),'http://homely.test/fixture-room.png');
 assert.equal(await page.locator('#assistant-panel').isVisible(),true);
 assert.equal(await page.locator('#assistant-panel').getAttribute('data-voice-phase'),'idle');
 assert.doesNotMatch(await page.locator('#assistant-panel').innerText(),/Listening/);
 await page.getByRole('button',{name:'Keep some furniture',exact:true}).click();await page.getByRole('button',{name:'Continue with this photo'}).click();await page.getByRole('button',{name:'Skip for now',exact:true}).click();await page.getByRole('button',{name:'Can’t select it? Tell us what to keep'}).click();await page.getByLabel('Piece name').fill('Existing table');await page.getByLabel('I confirm this is the piece').check();await page.getByRole('button',{name:'Keep this piece'}).click();await page.locator('#detail-dialog').waitFor({state:'hidden'});
 await page.locator('#assistant-message').focus();
 await page.getByLabel('Your message / editable transcript').fill('A draft, not a sent action');
 await page.locator('.mobile-nav [data-view="findings"]').click();
 await page.locator('.mobile-nav [data-view="workspace"]').click();
 assert.equal(await page.getByLabel('Your message / editable transcript').inputValue(),'A draft, not a sent action');
 assert.equal(requests.filter(r=>r.p.endsWith('/assistant')||r.p==='/api/transcriptions').length,0);
 assert.deepEqual(errors,[]);await context.close();
});

test('mobile Room keeps photo utilities and sourcing accessible behind secondary affordances',async()=>{
 const {page,context,requests}=await setup({width:550,height:1000},{savedHistory:true});
 await openDetails(page);await page.locator('.room-canvas img').waitFor();
 assert.equal(await page.getByRole('button',{name:'Change photo',exact:true}).isVisible(),false);
 await page.locator('.room-photo-options > summary').click();
 assert.equal(await page.getByRole('button',{name:'Change photo',exact:true}).isVisible(),true);
 await page.getByRole('button',{name:'◇ Placement',exact:true}).click();
 assert.equal(requests.filter(r=>r.p.endsWith('/visualizations')&&r.method==='POST').length,0);
 await openBrief(page);await page.locator('.room-research-actions > summary').click();
 assert.equal(await page.getByRole('button',{name:'Find pieces for this room'}).isVisible(),true);
 await context.close();
});

for(const width of [390,1440])test(`clearance dialog saves cm, reopens inches, defers without writes at ${width}`,async()=>{
 const {page,context,requests,errors}=await setup({width,height:1000},{savedHistory:true});
 await openBrief(page);if(!await page.locator('#brief-editor details').evaluate(el=>el.open))await page.locator('#brief-editor details > summary').click();await page.getByRole('button',{name:'Check chair clearance',exact:true}).click();
 assert.deepEqual(errors,[]);await page.locator('#fit-dialog').waitFor({state:'visible'});await page.locator('#fit-form select[name=units]').selectOption('cm');
 await page.getByLabel('Table clearance',{exact:true}).fill('68.58');
 await page.getByRole('button',{name:'Save measurement',exact:true}).click();
 await page.locator('#fit-dialog').waitFor({state:'hidden'});
 const writes=requests.filter(r=>r.p.endsWith('/brief'));assert.equal(writes.at(-1).body.brief.measurements.tableUndersideIn,27);
 await page.reload();await openBrief(page);if(!await page.locator('#brief-editor details').evaluate(el=>el.open))await page.locator('#brief-editor details > summary').click();await page.getByRole('button',{name:'Check chair clearance',exact:true}).click();
 assert.equal(await page.getByLabel('Table clearance',{exact:true}).inputValue(),'27');
 await page.getByLabel('Table clearance',{exact:true}).fill('99');
 await page.getByRole('button',{name:'I’ll do this later',exact:true}).click();
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).length,writes.length);
 await openBrief(page);if(!await page.locator('#brief-editor details').evaluate(el=>el.open))await page.locator('#brief-editor details > summary').click();await page.getByRole('button',{name:'Check chair clearance',exact:true}).click();assert.equal(await page.getByLabel('Table clearance',{exact:true}).inputValue(),'27');
 await context.close();
});

test('guided keep journey records explicit objects, categories, unknowns and gate without paid calls',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844});
 await page.getByLabel('Type or say a room',{exact:true}).fill('Dining room');await page.locator('#room-name-form button[type=submit], #room-name-form button').first().click();
 await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();assert.equal(await page.locator('[data-furnishing][aria-pressed=true]').count(),0);assert.deepEqual(requests.filter(r=>r.p.endsWith('/brief')).at(-1).body.brief.journey.selectedCategories,[]);
 await page.getByRole('button',{name:'Keep some furniture',exact:true}).click();await page.getByRole('heading',{name:/Add your room photo/}).waitFor();
 await page.getByRole('button',{name:'Skip for now',exact:true}).click();await page.getByRole('button',{name:'Skip for now',exact:true}).click();
 await page.getByRole('button',{name:'Can’t select it? Tell us what to keep'}).click();await page.getByLabel('Piece name').fill('Oak table');await page.getByLabel('Exact model / variant, if known').fill('Family table');await page.getByLabel('I confirm this is the piece').check();await page.getByRole('button',{name:'Keep this piece'}).click();
 await page.locator('.retained-list strong').waitFor();assert.match(await page.locator('.retained-list').innerText(),/Oak table/);
 const retained=requests.filter(r=>r.p.endsWith('/brief')).at(-1).body.brief.journey.retainedObjects[0];assert.equal(retained.confirmed,true);assert.equal(retained.anchor,undefined);
 await page.getByRole('button',{name:'Decide later',exact:true}).click();await page.getByRole('heading',{name:'Personalize your search'}).waitFor();
 await page.locator('[data-setup-category="Dining chairs"]').click();await page.locator('[data-setup-category="Dining room lighting"]').click();
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).at(-1).body.brief.journey.selectedCategories.length,2);
 await page.getByRole('button',{name:'Show options'}).click();await page.getByRole('heading',{name:'Check the fit',exact:true}).waitFor();await page.getByRole('img',{name:'Measure tabletop height, the lowest edge under the table, and space between the table legs',exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:'View fit-qualified results'}).isDisabled(),true);
 assert.equal(requests.filter(r=>/\/assistant$|\/research$|\/transcriptions$/.test(r.p)).length,0);
 await page.reload();await page.getByRole('heading',{name:'Check the fit',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);await context.close();
});
test('fresh journey skips keeping, preserves drafts and opens explicitly labelled inspiration',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true,reviewData:true});
 await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();assert.equal(await page.locator('.setup-hero img').count(),0);
 await page.getByRole('button',{name:'Edit brief',exact:true}).click();await page.getByLabel('Location',{exact:true}).fill('Unsaved location');
 await page.getByRole('button',{name:'Furnish from scratch',exact:true}).click();await page.getByRole('button',{name:'Continue with this photo'}).click();await page.getByRole('button',{name:'Skip for now',exact:true}).click();
 await page.getByRole('heading',{name:'Personalize your search'}).waitFor();assert.equal(await page.getByRole('heading',{name:/Choose what stays/}).count(),0);
 assert.equal(requests.filter(r=>r.p.endsWith('/brief')).at(-1).body.brief.journey.keepingDecision,'fresh');
 await page.getByRole('button',{name:'Edit brief',exact:true}).click();assert.equal(await page.getByLabel('Location',{exact:true}).inputValue(),'Unsaved location');
 await page.locator('[data-setup-category]').first().click();await page.getByRole('button',{name:'Show options'}).click();await page.getByRole('img',{name:'Measure the usable room width and depth for a rectangular furniture grid, and the maximum furniture height',exact:true}).waitFor();assert.doesNotMatch(await page.locator('.journey-fit-diagram').textContent(),/table|apron/i);await page.getByRole('button',{name:'Browse inspiration instead'}).click();
 await page.getByText('Inspiration · physical fit is not confirmed',{exact:true}).waitFor();assert.equal(requests.filter(r=>r.p.endsWith('/research')).length,0);assert.deepEqual(errors,[]);await context.close();
});
test('auth password visibility and recovery use email only with no automatic resend',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{cloud:true});await page.getByLabel('Email',{exact:true}).fill('fixture@example.invalid');await page.getByLabel('Password',{exact:true}).fill('fixture password');
 await page.getByRole('button',{name:'Show',exact:true}).click();assert.equal(await page.locator('[name=password]').getAttribute('type'),'text');await page.getByRole('button',{name:'Hide',exact:true}).click();assert.equal(await page.locator('[name=password]').getAttribute('type'),'password');
 assert.equal(await page.locator('#auth-resend').isVisible(),false);await page.getByRole('button',{name:'Forgot password?'}).click();await page.waitForFunction(()=>document.querySelector('#auth-message').textContent.includes('Password recovery is not connected'));
 assert.equal(requests.filter(r=>r.p==='/api/auth/recover').length,0);assert.equal(requests.filter(r=>r.p==='/api/auth/resend').length,0);assert.deepEqual(errors,[]);await context.close();
});
test('room picker has one composer and voice transcript requires explicit room confirmation',async()=>{
 const {page,context,requests,errors}=await setup({width:390,height:844},{media:'success'});await page.getByRole('heading',{name:'Which room are we working on?'}).waitFor();assert.equal(await page.locator('#assistant-panel').isVisible(),false);
 await page.locator('[data-room-voice]').click();await page.locator('#voice-consent-checkbox').check();await page.getByRole('button',{name:'Start recording',exact:true}).click();await page.getByRole('button',{name:'Stop & review transcript'}).click();await page.waitForFunction(()=>document.querySelector('#room-name').value==='Set quantity to four');
 assert.equal(requests.filter(r=>r.p==='/api/projects'&&r.method==='POST').length,0);assert.equal(await page.locator('#assistant-panel').isVisible(),false);await page.locator('#room-name').fill('Home office');await page.locator('#room-name-form button').first().click();await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();assert.equal(requests.find(r=>r.p==='/api/projects'&&r.method==='POST').body.name,'Home office');assert.deepEqual(errors,[]);await context.close();
});
test('undefined source URLs never become links and unconnected watches never activate',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true});await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();assert.equal(await page.evaluate(()=>safeUrl(undefined)), '');assert.equal(await page.evaluate(()=>safeUrl('')), '');
 await page.evaluate(()=>watchDialog('lead-1'));await page.getByRole('heading',{name:'Watch price updates for this item?'}).waitFor();assert.equal(await page.locator('#watch-enable').isDisabled(),true);assert.match(await page.locator('#detail-content').innerText(),/no alert or watch has been enabled/);assert.equal(requests.filter(r=>r.p.endsWith('/watches')&&r.method==='POST').length,0);assert.deepEqual(errors,[]);await context.close();
});
test('optional room upload saves original without granting image-provider consent',async()=>{
 const {page,context,requests,errors}=await setup();await createRoom(page,'Photo consent room');await page.getByRole('button',{name:'Keep some furniture',exact:true}).click();await page.getByRole('button',{name:'Upload a photo',exact:true}).click();
 const image={name:'fixture.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jY1cAAAAASUVORK5CYII=','base64')};await page.getByLabel('Room photo',{exact:true}).setInputFiles(image);assert.equal(await page.locator('#room-form [name=consent]').isChecked(),false);await page.getByRole('button',{name:'Save room photo'}).click();await page.getByText('Room photo saved. Your original is preserved.',{exact:true}).waitFor();const upload=requests.find(r=>r.p.endsWith('/room'));assert.equal(upload.body.uploadConsent,true);assert.equal(upload.body.consent,false);assert.equal(requests.filter(r=>r.p.endsWith('/visualizations')&&r.method==='POST').length,0);assert.deepEqual(errors,[]);await context.close();
});
test('fit results exclude candidates without independent passing checks and retain a measurement-review route',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true,fitPassed:true,fitSecondBlocked:true});await page.getByRole('button',{name:'Keep some furniture',exact:true}).click();await page.getByRole('button',{name:'Continue with this photo'}).click();await page.getByRole('button',{name:'Skip for now',exact:true}).click();await page.getByRole('button',{name:'Decide later',exact:true}).click();await page.locator('[data-setup-category]').first().click();await page.getByRole('button',{name:'Show options'}).click();await page.waitForFunction(()=>!document.querySelector('[data-fit-results]').disabled);await page.getByRole('button',{name:'View fit-qualified results'}).click();
 await page.getByText('Fit-qualified results · only passing dimensional checks',{exact:true}).waitFor();assert.match(await page.locator('#view').textContent(),/Price watches require separate opt-in/);assert.match(await page.locator('#view').innerText(),/The shown candidates passed their recorded dimensional checks/);assert.doesNotMatch(await page.locator('#view').innerText(),/passing fit and availability evidence|continuous monitoring are not implemented/);await page.locator('.candidate').waitFor();assert.equal(await page.locator('.candidate').count(),1);assert.match(await page.locator('.candidate').innerText(),/Oak dining chair/);assert.doesNotMatch(await page.locator('.candidate').innerText(),/Linen dining chair/);assert.ok((await page.locator('.candidate').boundingBox()).y<400,'Product card should appear near the top of desktop results');assert.equal(await page.locator('.empty-view').count(),0);await page.locator('.missing-fit-details > summary').click();await page.getByRole('button',{name:'Review measurements: Linen dining chair'}).click();await page.getByRole('heading',{name:'Exact candidate fit evidence'}).waitFor();assert.equal(requests.filter(r=>r.p.endsWith('/research')).length,0);assert.deepEqual(errors,[]);await context.close();
});
test('recovery explicitly submits verified-host token hash, never stores secrets, and resend stays contextual',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{cloud:true,authFeatures:true});await page.getByRole('heading',{name:'Welcome back'}).waitFor();await page.getByLabel('Email',{exact:true}).fill('fixture@example.invalid');await page.getByRole('button',{name:'Forgot password?'}).click();await page.getByText('If this address is eligible, check your email.',{exact:true}).waitFor();assert.deepEqual(requests.find(r=>r.p==='/api/auth/recover').body,{email:'fixture@example.invalid'});assert.equal(await page.locator('#auth-resend').isVisible(),false);
 await page.getByRole('button',{name:'Have a recovery email?'}).click();const hash='a'.repeat(64);await page.getByLabel('Recovery email link or token hash').fill('https://attacker.invalid/auth/v1/verify?token='+hash+'&type=recovery');await page.getByLabel('New password',{exact:true}).fill('only-a-test-password');await page.getByRole('button',{name:'Set new password'}).click();await page.getByText('Use the password recovery link from your Homely email.',{exact:true}).waitFor();assert.equal(requests.filter(r=>r.p==='/api/auth/reset').length,0);
 await page.getByLabel('Recovery email link or token hash').fill('https://bbwmwwupvqajidqznsly.supabase.co/auth/v1/verify?token='+hash+'&type=recovery');await page.getByRole('button',{name:'Show password',exact:true}).click();assert.equal(await page.locator('[name=newPassword]').getAttribute('type'),'text');await page.getByRole('button',{name:'Set new password'}).click();await page.getByText('Password updated. Sign in with your new password.',{exact:true}).waitFor();assert.deepEqual(requests.find(r=>r.p==='/api/auth/reset').body,{tokenHash:hash,newPassword:'only-a-test-password'});assert.equal(await page.evaluate(()=>JSON.stringify({...sessionStorage,...localStorage}).includes('only-a-test-password')),false);assert.equal(await page.evaluate(()=>JSON.stringify({...sessionStorage,...localStorage}).includes('a'.repeat(64))),false);assert.equal(await page.locator('[name=recovery]').count(),0);assert.deepEqual(errors,[]);await context.close();
});
test('fit units convert actual dimensions and tolerances without changing quantity or row counts',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true});await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();await page.evaluate(()=>fitEditor());const form=page.locator('#fit-evidence-form');await form.locator('[name=quantity]').fill('6');await form.locator('[name=lowestApronHeight]').fill('27');await form.locator('[name=chairGap]').fill('2');await form.locator('[name=count0]').fill('3');await form.locator('[name=legSpacing0]').fill('70');await form.locator('[name=unit]').selectOption('cm');assert.equal(Number(await form.locator('[name=lowestApronHeight]').inputValue()),68.58);assert.equal(Number(await form.locator('[name=chairGap]').inputValue()),5.08);assert.equal(await form.locator('[name=count0]').inputValue(),'3');assert.equal(await form.locator('[name=quantity]').inputValue(),'6');await form.locator('[name=unit]').selectOption('in');assert.equal(Number(await form.locator('[name=lowestApronHeight]').inputValue()),27);assert.equal(Number(await form.locator('[name=legSpacing0]').inputValue()),70);assert.equal(requests.filter(r=>r.p.endsWith('/brief')).length,0);assert.deepEqual(errors,[]);await context.close();
});
test('watch subscription is separate opt-in, shows local delivery limits, and can be cancelled',async()=>{
 const {page,context,requests,errors}=await setup(undefined,{savedHistory:true,watchFeatures:true});await page.getByRole('heading',{name:'How would you like to begin?'}).waitFor();await page.evaluate(()=>watchDialog('lead-1'));assert.equal(requests.filter(r=>r.p.endsWith('/watches')&&r.method==='POST').length,0);assert.match(await page.locator('#detail-content').innerText(),/email and push notifications are not connected/);await page.getByRole('button',{name:'Enable price watch',exact:true}).click();await page.getByRole('button',{name:'Turn off watch'}).waitFor();const body=requests.find(r=>r.p==='/api/projects/p1/watches').body;assert.equal(body.enabled,true);assert.equal(body.candidateId,'lead-1');assert.equal(body.owner,undefined);assert.match(await page.locator('.watch-row').innerText(),/2026/);await page.getByRole('button',{name:'Mark as read'}).click();await page.getByText('Read',{exact:true}).waitFor();await page.getByRole('button',{name:'Turn off watch'}).click();await page.getByText(/cancelled · Last check/).waitFor();assert.equal(requests.filter(r=>r.p==='/api/watches/w1/cancel').length,1);assert.equal(requests.filter(r=>r.p==='/api/notifications/n1/read').length,1);assert.deepEqual(errors,[]);await context.close();
});
