"""Evidence-bound remediation routing. Guidance never grants execution authority."""
import hashlib
import json
from fastapi import APIRouter,Depends,HTTPException,Query
from .auth import current,member
from .db import database
from .models import Finding,Asset,Job
from .analyst import RULES

router=APIRouter(tags=['Universal FastFix guidance'])
PLATFORMS={
    'netlify':('hosting_guidance','Existing netlify.toml nosniff proposals are supported through the separately approved GitHub workflow. Static responses only; functions, SSR, proxies and competing _headers require manual review.'),
    'unknown':('engineering_review','Identify the responsible application, hosting layer and maintainer before changing configuration.'),
    'github':('developer_handoff','Confirm the repository actually deploys this asset. Existing draft-PR support is limited to reviewed vercel.json nosniff proposals.'),
    'gitlab':('developer_handoff','Have a maintainer create a reviewed merge request. No live GitLab write adapter is implemented.'),
    'wordpress':('cms_guidance','Review active plugins, theme and hosting settings in an owned staging copy. The ownership plugin does not authorize configuration or PHP changes.'),
    'woocommerce':('cms_guidance','Use a staging store and test checkout, sessions and payment-provider redirects before changing cookie or browser policy.'),
    'joomla':('cms_guidance','Ask the CMS maintainer to review extension, template and hosting configuration on staging.'),
    'drupal':('cms_guidance','Ask the CMS maintainer to review modules, caching and hosting configuration on staging.'),
    'php':('developer_handoff','Locate the responsible PHP response/session configuration or reverse proxy; do not modify unrelated endpoints.'),
    'laravel':('developer_handoff','Review application middleware, session configuration and reverse-proxy behavior; validate configuration caches on staging.'),
    'python':('developer_handoff','Identify the framework middleware or reverse proxy that emits the observed response.'),
    'django':('developer_handoff','Review security middleware, cookie settings and proxy trust; test authentication and CSRF behavior.'),
    'fastapi':('developer_handoff','Review response middleware, CORS configuration and the TLS-terminating proxy; test the affected routes.'),
    'node':('developer_handoff','Review response middleware and hosting headers; validate application and proxy behavior together.'),
    'express':('developer_handoff','Review Express middleware ordering, response headers and proxy trust; test authentication and assets.'),
    'nextjs':('developer_handoff','Review Next.js headers, route handlers and hosting overrides. Confirm which layer produces the affected response.'),
    'react':('developer_handoff','Browser code alone cannot set server response headers. Review the deployment server or CDN configuration.'),
    'vue':('developer_handoff','Review the deployment server or CDN; client components do not control server response headers.'),
    'nuxt':('developer_handoff','Review server route rules, middleware and hosting overrides on the affected route.'),
    'java':('developer_handoff','Locate servlet/filter or gateway configuration and test affected application routes.'),
    'spring':('developer_handoff','Review the security filter chain, CORS and session configuration; preserve application authentication behavior.'),
    'aspnet':('developer_handoff','Review ASP.NET middleware and IIS/reverse-proxy configuration; validate affected endpoints.'),
    'rails':('developer_handoff','Review Rails security headers, session configuration and front-end hosting compatibility.'),
    'static':('hosting_guidance','Change response configuration at the serving host/CDN, not inside a static HTML document.'),
    'cpanel':('hosting_guidance','Ask the authorized hosting administrator to identify the web server and supported configuration mechanism; preserve the original file.'),
    'plesk':('hosting_guidance','Ask the hosting administrator to review the applicable virtual-host configuration and staging compatibility.'),
    'cloud':('hosting_guidance','Identify the load balancer, CDN or container ingress responsible for this response; review infrastructure changes before deployment.'),
    'shopify':('provider_action','Use supported platform settings or support escalation; do not assume access to server headers or infrastructure.'),
    'wix':('provider_action','Use supported platform settings or provider support. Direct server configuration is not available through AEGIS.'),
    'webflow':('provider_action','Review supported hosting settings or provider support; no direct platform changes are implemented.'),
    'custom':('engineering_review','Have the application maintainer identify the responsible code/configuration and provide a minimal reviewable change.'),
}

def build_plan(finding,asset,platform):
    if platform not in PLATFORMS:raise ValueError('Unsupported platform selection.')
    method,context=PLATFORMS[platform]
    rule=finding.rule.split('@')[0];known=RULES.get(rule)
    if not known:method='further_investigation'
    action=known[2] if known else 'A qualified engineer must validate this detector, evidence and affected component before proposing a fix.'
    plan={
        'version':'fastfix-guidance-v1','mode':'deterministic reviewed guidance; not generative AI repair',
        'finding_id':finding.id,'asset_id':asset.id,'assessment_id':finding.job_id,
        'origin':asset.origin,'rule':finding.rule,'observed_status':finding.status,
        'evidence':{'summary':finding.evidence,'confidence':finding.confidence,'last_observed':finding.last_observed},
        'platform':platform,'platform_verified':False,'method':method,
        'root_cause':'The assessment recorded a security configuration observation; the responsible component, actual root cause and exploitability have not been established.',
        'recommended_action':action,'platform_guidance':context,
        'missing_information':['Confirmed technology and version','Responsible source/configuration layer','Authorized staging environment and deployment revision','Application compatibility requirements'],
        'compatibility_risks':['Browser policy changes can break scripts, embedding and third-party integrations.','Cookie changes can affect login, checkout and cross-site authentication.','HTTPS/HSTS changes require valid certificates and coverage of affected hosts.'],
        'validation_required':['Review syntax and configuration with the responsible platform tooling.','Run affected application tests and build in an isolated environment.','Verify the approved deployment revision and application behavior on separately authorized staging.','After customer-controlled deployment, authorize the complete applicable security profile and compare every supported baseline finding.'],
        'capabilities':{'guidance':True,'reads_customer_source':False,'generates_patch':False,'executes_commands':False,'deploys':False,'remote_rollback':False},
        'tests_passed':[],'tests_failed':[],'tests_not_performed':['Customer source/build tests','Staging deployment and behavior','Post-deployment reassessment'],
        'backup_scope':'No customer backup created by this guidance endpoint. Establish and test a deployment-specific backup/rollback plan before approval.',
        'approval':'Guidance is not approval. Modification requires separate exact-change/asset approval and MFA through the supported remediation workflow.',
        'next_step':'Request an engineer-reviewed remediation scope; existing GitHub draft-PR flow is optional.',
        'fix_verified':False,'paid_service_required':False,
    }
    if known and rule=='header.nosniff' and platform in ('github','nextjs','static'):
        plan['optional_supported_adapter']={'name':'github_vercel_nosniff','availability':'conditional; separately authorized connected repository and accepted remediation scope required','entrypoint':'/repository-patches','limitations':'Existing vercel.json only; no application tests or deployment implied.'}
    if known and rule=='header.nosniff' and platform=='netlify':
        plan['optional_supported_adapter']={'name':'github_netlify_nosniff','adapter':'netlify','availability':'conditional; separately authorized connected repository and accepted remediation scope required','entrypoint':'/repository-patches','limitations':'Existing root netlify.toml; static responses only. No application tests, deployment or fix verification implied.'}
    plan['content_sha256']=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return plan

@router.get('/findings/{finding_id}/fastfix')
def guidance(finding_id:str,platform:str=Query(default='unknown',max_length=30),u=Depends(current),db=Depends(database)):
    f=db.get(Finding,finding_id)
    if not f:raise HTTPException(404,'Finding not found.')
    member(db,u,f.org_id)
    asset=db.get(Asset,f.asset_id);job=db.get(Job,f.job_id)
    if not asset or asset.org_id!=f.org_id or not job or job.org_id!=f.org_id or job.asset_id!=asset.id:
        raise HTTPException(409,'Consistent assessment and asset evidence is required.')
    try:return build_plan(f,asset,platform)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
