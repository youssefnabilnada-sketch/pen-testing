import time
import uuid
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, JSON, Boolean, Float, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid():
    return str(uuid.uuid4())

class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created: Mapped[float] = mapped_column(Float, default=time.time)

class User(Identity, Base):
    __tablename__ = 'users'
    display_name: Mapped[str] = mapped_column(String(100),default='',server_default='')
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password: Mapped[str] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    superadmin: Mapped[bool] = mapped_column(Boolean, default=False)

class LoginSession(Identity, Base):
    __tablename__ = 'sessions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf: Mapped[str] = mapped_column(String(100))
    expires: Mapped[float] = mapped_column(Float)

class EmailToken(Identity, Base):
    __tablename__ = 'email_tokens'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    purpose: Mapped[str] = mapped_column(String(20))
    expires: Mapped[float] = mapped_column(Float)

class Organization(Identity, Base):
    __tablename__ = 'organizations'
    name: Mapped[str] = mapped_column(String(120))

class Membership(Identity, Base):
    __tablename__ = 'memberships'
    __table_args__ = (UniqueConstraint('org_id', 'user_id'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    role: Mapped[str] = mapped_column(String(30))

class Asset(Identity, Base):
    __tablename__ = 'assets'
    __table_args__ = (UniqueConstraint('org_id', 'origin'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    origin: Mapped[str] = mapped_column(String(300))
    verified_until: Mapped[float] = mapped_column(Float, default=0)

class Challenge(Identity, Base):
    __tablename__ = 'challenges'
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    method: Mapped[str] = mapped_column(String(20))
    token: Mapped[str] = mapped_column(String(100))
    expires: Mapped[float] = mapped_column(Float)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)

class Authorization(Identity, Base):
    __tablename__ = 'authorizations'
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    scope: Mapped[dict] = mapped_column(JSON)
    expires: Mapped[float] = mapped_column(Float)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    terms_version: Mapped[str] = mapped_column(String(30), default='2026-10-v1')

class Job(Identity, Base):
    __tablename__ = 'jobs'
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    authorization_id: Mapped[str] = mapped_column(ForeignKey('authorizations.id'))
    status: Mapped[str] = mapped_column(String(30), default='queued', index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    cancel: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    finished: Mapped[float | None] = mapped_column(Float)
    observations: Mapped[list] = mapped_column(JSON, default=list)

class Finding(Identity, Base):
    __tablename__ = 'findings'
    __table_args__ = (UniqueConstraint('asset_id', 'rule'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'))
    rule: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    severity: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[str] = mapped_column(String(20), default='high')
    evidence: Mapped[str] = mapped_column(Text)
    remediation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='open')
    last_observed: Mapped[float] = mapped_column(Float, default=time.time)

class FindingHistory(Identity, Base):
    __tablename__ = 'finding_history'
    finding_id: Mapped[str] = mapped_column(ForeignKey('findings.id'), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey('jobs.id'))
    status: Mapped[str] = mapped_column(String(30))

class Report(Identity, Base):
    __tablename__ = 'reports'
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'), unique=True)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)

class Remediation(Identity, Base):
    __tablename__ = 'remediations'
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey('findings.id'))
    status: Mapped[str] = mapped_column(String(30), default='requested')
    estimate: Mapped[str] = mapped_column(Text)
    scope: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default='EGP')
    accepted_at: Mapped[float | None] = mapped_column(Float)
    assigned_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))

class Message(Identity, Base):
    __tablename__ = 'messages'
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    remediation_id: Mapped[str] = mapped_column(ForeignKey('remediations.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    body: Mapped[str] = mapped_column(Text)
    internal: Mapped[bool] = mapped_column(Boolean, default=False)

class Audit(Identity, Base):
    __tablename__ = 'audit'
    org_id: Mapped[str | None] = mapped_column(ForeignKey('organizations.id'), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(120))
    target: Mapped[str] = mapped_column(String(100))

class Setting(Base):
    __tablename__ = 'settings'
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[bool] = mapped_column(Boolean)

class IntelligenceSource(Base):
    __tablename__ = 'intelligence_sources'
    key: Mapped[str] = mapped_column(String(30), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    interval_hours: Mapped[int] = mapped_column(Integer, default=6)
    last_attempt: Mapped[float | None] = mapped_column(Float)
    last_success: Mapped[float | None] = mapped_column(Float)
    next_due: Mapped[float] = mapped_column(Float, default=0)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    cursor: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

class SyncRun(Identity, Base):
    __tablename__ = 'intelligence_sync_runs'
    source: Mapped[str] = mapped_column(ForeignKey('intelligence_sources.key'), index=True)
    status: Mapped[str] = mapped_column(String(20), default='running')
    finished: Mapped[float | None] = mapped_column(Float)
    records: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)

class Advisory(Identity, Base):
    __tablename__ = 'advisories'
    identifier: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(400))
    severity: Mapped[str] = mapped_column(String(20), default='unknown')
    exploited: Mapped[bool] = mapped_column(Boolean, default=False)
    updated: Mapped[float] = mapped_column(Float, default=time.time, index=True)

class AdvisoryAlias(Base):
    __tablename__ = 'advisory_aliases'
    alias: Mapped[str] = mapped_column(String(100), primary_key=True)
    advisory_id: Mapped[str] = mapped_column(ForeignKey('advisories.id'), index=True)

class KnowledgeRevision(Identity, Base):
    __tablename__ = 'knowledge_revisions'
    __table_args__ = (UniqueConstraint('advisory_id', 'source', 'digest'),)
    advisory_id: Mapped[str] = mapped_column(ForeignKey('advisories.id'), index=True)
    source: Mapped[str] = mapped_column(ForeignKey('intelligence_sources.key'), index=True)
    digest: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSON)
    source_updated: Mapped[str] = mapped_column(String(80))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    approved_at: Mapped[float | None] = mapped_column(Float)
    current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

class InventoryItem(Identity, Base):
    __tablename__ = 'inventory_items'
    __table_args__ = (UniqueConstraint('asset_id', 'ecosystem', 'package'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    ecosystem: Mapped[str] = mapped_column(String(30))
    package: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(100))
    evidence: Mapped[str] = mapped_column(String(500))
    updated: Mapped[float] = mapped_column(Float, default=time.time)

class AdvisoryImpact(Identity, Base):
    __tablename__ = 'advisory_impacts'
    __table_args__ = (UniqueConstraint('inventory_id', 'advisory_id'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    inventory_id: Mapped[str] = mapped_column(ForeignKey('inventory_items.id'))
    advisory_id: Mapped[str] = mapped_column(ForeignKey('advisories.id'))
    status: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    revision_ids: Mapped[list] = mapped_column(JSON)
    updated: Mapped[float] = mapped_column(Float, default=time.time)

class Notification(Identity, Base):
    __tablename__ = 'notifications'
    __table_args__ = (UniqueConstraint('org_id', 'dedupe_key'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(250))
    kind: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(250))
    detail: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(String(100))
    read: Mapped[bool] = mapped_column(Boolean, default=False)

class AssessmentSchedule(Identity, Base):
    __tablename__ = 'assessment_schedules'
    __table_args__ = (UniqueConstraint('asset_id'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'))
    authorization_id: Mapped[str] = mapped_column(ForeignKey('authorizations.id'))
    cadence: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    on_advisory: Mapped[bool] = mapped_column(Boolean, default=False)
    reverify: Mapped[bool] = mapped_column(Boolean, default=False)
    next_due: Mapped[float] = mapped_column(Float)
    last_run: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default='scheduled')
    last_job_id: Mapped[str | None] = mapped_column(ForeignKey('jobs.id'))

class QueueOutbox(Identity, Base):
    __tablename__ = 'queue_outbox'
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'), unique=True)
    dispatched: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt: Mapped[float] = mapped_column(Float, default=0)
    error: Mapped[str | None] = mapped_column(Text)

class Retest(Identity, Base):
    __tablename__ = 'retests'
    __table_args__ = (UniqueConstraint('job_id'),)
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    remediation_id: Mapped[str] = mapped_column(ForeignKey('remediations.id'), index=True)
    baseline_job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'))
    job_id: Mapped[str | None] = mapped_column(ForeignKey('jobs.id'))
    status: Mapped[str] = mapped_column(String(30), default='awaiting_approval')
    evidence: Mapped[str] = mapped_column(Text)
    rollback_plan: Mapped[str] = mapped_column(Text)
    staging_validation: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    comparison: Mapped[dict] = mapped_column(JSON, default=dict)

class DetectionRule(Base):
    __tablename__ = 'detection_rules'
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[str] = mapped_column(String(30))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    approved_at: Mapped[float | None] = mapped_column(Float)
    test_evidence: Mapped[str | None] = mapped_column(Text)

class FirebaseIdentity(Identity, Base):
    __tablename__ = 'firebase_identities'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True)
    project: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(128))
    __table_args__ = (UniqueConstraint('project', 'subject'),)

class TeamInvitation(Identity, Base):
    __tablename__ = 'team_invitations'
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'),index=True)
    email: Mapped[str] = mapped_column(String(254),index=True)
    role: Mapped[str] = mapped_column(String(30))
    invited_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    expires: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20),default='pending')
    accepted_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))

class SupportTicket(Identity, Base):
    __tablename__='support_tickets'
    org_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    subject: Mapped[str]=mapped_column(String(160))
    status: Mapped[str]=mapped_column(String(30),default='open',index=True)
    updated: Mapped[float]=mapped_column(Float,default=time.time)

class SupportMessage(Identity, Base):
    __tablename__='support_messages'
    ticket_id: Mapped[str]=mapped_column(ForeignKey('support_tickets.id'),index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    body: Mapped[str]=mapped_column(Text)
    internal: Mapped[bool]=mapped_column(Boolean,default=False)
    staff: Mapped[bool]=mapped_column(Boolean,default=False)

class MfaState(Base):
    __tablename__='mfa_states'
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    secret: Mapped[str]=mapped_column(Text)
    enabled: Mapped[bool]=mapped_column(Boolean,default=False)
    expires: Mapped[float]=mapped_column(Float)
    enrollment_session: Mapped[str]=mapped_column(String(64))
    last_counter: Mapped[int]=mapped_column(Integer,default=-1)

class RecoveryCode(Base):
    __tablename__='mfa_recovery_codes'
    digest: Mapped[str]=mapped_column(String(64),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'),index=True)
    used: Mapped[bool]=mapped_column(Boolean,default=False)

class Attachment(Identity, Base):
    __tablename__='attachments'
    __table_args__=(CheckConstraint('(support_ticket_id IS NULL) <> (remediation_id IS NULL)',name='one_attachment_parent'),)
    support_ticket_id: Mapped[str | None]=mapped_column(ForeignKey('support_tickets.id'),index=True)
    remediation_id: Mapped[str | None]=mapped_column(ForeignKey('remediations.id'),index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    filename: Mapped[str]=mapped_column(String(100))
    content: Mapped[str]=mapped_column(Text)
    size: Mapped[int]=mapped_column(Integer)
    internal: Mapped[bool]=mapped_column(Boolean,default=False)

class NotificationPreference(Base):
    __tablename__='notification_preferences'
    org_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    enabled_kinds: Mapped[list]=mapped_column(JSON)

class NotificationRead(Base):
    __tablename__='notification_reads'
    notification_id: Mapped[str]=mapped_column(ForeignKey('notifications.id'),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)

class GitHubState(Identity,Base):
    __tablename__='github_states'
    org_id:Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    digest:Mapped[str]=mapped_column(String(64),unique=True)
    expires:Mapped[float]=mapped_column(Float)
    used:Mapped[bool]=mapped_column(Boolean,default=False)

class GitHubConnection(Identity,Base):
    __tablename__='github_connections'
    org_id:Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    account_id:Mapped[str]=mapped_column(String(40))
    login:Mapped[str]=mapped_column(String(100))
    encrypted_token:Mapped[str]=mapped_column(Text)
    expires:Mapped[float]=mapped_column(Float)
    revoked:Mapped[bool]=mapped_column(Boolean,default=False)

class RepositoryPatch(Identity,Base):
    __tablename__='repository_patches'
    org_id:Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    connection_id:Mapped[str]=mapped_column(ForeignKey('github_connections.id'))
    remediation_id:Mapped[str]=mapped_column(ForeignKey('remediations.id'))
    repository:Mapped[str]=mapped_column(String(220))
    base_branch:Mapped[str]=mapped_column(String(200))
    base_sha:Mapped[str]=mapped_column(String(64))
    file_sha:Mapped[str]=mapped_column(String(64),default='')
    proposed_content:Mapped[str]=mapped_column(Text)
    diff:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(40),default='review_required')
    test_evidence:Mapped[dict]=mapped_column(JSON,default=dict)
    pull_number:Mapped[int|None]=mapped_column(Integer,nullable=True)
    approved_by:Mapped[str|None]=mapped_column(ForeignKey('users.id'),nullable=True)

class HealthMonitor(Identity, Base):
    __tablename__ = 'health_monitors'
    org_id: Mapped[str] = mapped_column(ForeignKey('organizations.id'), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), unique=True)
    authorization_id: Mapped[str] = mapped_column(ForeignKey('authorizations.id'))
    interval_seconds: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    next_due: Mapped[float] = mapped_column(Float)
    last_status: Mapped[str] = mapped_column(String(30), default='pending')

class HealthSample(Identity, Base):
    __tablename__ = 'health_samples'
    monitor_id: Mapped[str] = mapped_column(ForeignKey('health_monitors.id'), index=True)
    status: Mapped[str] = mapped_column(String(30))
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tls_expires: Mapped[float | None] = mapped_column(Float, nullable=True)
    incident: Mapped[bool] = mapped_column(Boolean, default=False)

class LaunchReview(Identity, Base):
    __tablename__='launch_reviews'
    org_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    repository: Mapped[str]=mapped_column(String(220))
    revision: Mapped[str]=mapped_column(String(40))
    result: Mapped[dict]=mapped_column(JSON)

class AgencyGrant(Identity, Base):
    __tablename__='agency_grants'
    __table_args__=(UniqueConstraint('agency_id','client_id'),)
    agency_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    client_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'))
    expires: Mapped[float]=mapped_column(Float)
    revoked: Mapped[bool]=mapped_column(Boolean,default=False)
    reports: Mapped[bool]=mapped_column(Boolean,default=False)

class AgencyBrand(Identity, Base):
    __tablename__='agency_brands'
    org_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'),unique=True)
    settings: Mapped[dict]=mapped_column(JSON)

class AlertSubscription(Identity, Base):
    __tablename__='alert_subscriptions'
    __table_args__=(UniqueConstraint('org_id','user_id'),)
    org_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'))
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    kinds: Mapped[list]=mapped_column(JSON)

class EmailDelivery(Identity, Base):
    __tablename__='email_deliveries'
    __table_args__=(UniqueConstraint('notification_id','user_id'),)
    notification_id: Mapped[str]=mapped_column(ForeignKey('notifications.id'))
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'),index=True)
    status: Mapped[str]=mapped_column(String(30),default='pending')
    attempts: Mapped[int]=mapped_column(Integer,default=0)
    next_due: Mapped[float]=mapped_column(Float,default=0)
    error: Mapped[str]=mapped_column(String(200),default='')

class PatchBackup(Identity, Base):
    __tablename__='patch_backups'
    patch_id: Mapped[str]=mapped_column(ForeignKey('repository_patches.id'),unique=True)
    encrypted_content: Mapped[str]=mapped_column(Text)
    sha256: Mapped[str]=mapped_column(String(64))
    restore_verified: Mapped[bool]=mapped_column(Boolean,default=False)

class Lead(Identity, Base):
    __tablename__='leads'
    org_id: Mapped[str]=mapped_column(ForeignKey('organizations.id'),index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    kind: Mapped[str]=mapped_column(String(20))
    message: Mapped[str]=mapped_column(Text)
    contact_consent: Mapped[bool]=mapped_column(Boolean,default=False)
    status: Mapped[str]=mapped_column(String(30),default='new')
    followup_at: Mapped[float|None]=mapped_column(Float,nullable=True)
    history: Mapped[list]=mapped_column(JSON,default=list)
    invite_digest: Mapped[str|None]=mapped_column(String(64),nullable=True)
    invite_expires: Mapped[float|None]=mapped_column(Float,nullable=True)

class EvidenceSeal(Identity, Base):
    __tablename__='evidence_seals'
    report_id: Mapped[str]=mapped_column(ForeignKey('reports.id'),unique=True)
    sha256: Mapped[str]=mapped_column(String(64))

class EvidenceLegalHold(Identity, Base):
    """Auditable owner/admin preservation request; never deletes evidence."""
    __tablename__ = 'evidence_legal_holds'
    report_id: Mapped[str] = mapped_column(ForeignKey('reports.id'), index=True)
    reason: Mapped[str] = mapped_column(String(500))
    placed_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    released_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    released_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
