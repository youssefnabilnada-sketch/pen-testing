'use client';
import {ArrowRight,BookOpen,FileCheck2,Globe2,HelpCircle,LockKeyhole,ScanLine,Settings2,ShieldCheck,Sparkles,Users} from 'lucide-react';
import {useExperience} from './Experience';

type Tool='Threat Intelligence'|'API Assessment'|'Launch Guard'|'Evidence Vault'|'Agency'|'Onboarding'|'Team'|'Support'|'Account security';
const tools:Record<Tool,{
 eyebrow:[string,string];headline:[string,string];desc:[string,string];action:[string,string];go:string;icon:typeof ShieldCheck;
}>={
 'Threat Intelligence':{eyebrow:['GLOBAL SECURITY INTELLIGENCE','المعلومات الأمنية العالمية'],headline:['New advisories, with the evidence to trust them.','أحدث النشرات الأمنية مع دليل تحديثها الفعلي.'],desc:['Trusted feeds refresh on a configured schedule. Source records and potential matches are not confirmed findings on your site.','المصادر الموثوقة بتتحدث حسب الجدول المضبوط. النشرات والتطابقات المحتملة مش دليل على ثغرات مؤكدة في موقعك.'],action:['My findings','نتائج موقعي'],go:'Findings',icon:Sparkles},
 'API Assessment':{eyebrow:['AUTHORIZED API CHECKS','فحص API بتصريح'],headline:['Review only the API paths you authorize.','افحص فقط مسارات API اللي توافق عليها.'],desc:['Choose a verified origin, review non-destructive public GET paths and approve a bounded assessment.','اختار موقع مثبت الملكية وحدد مسارات GET عامة وآمنة ووافق على نطاق الفحص المحدود.'],action:['My websites','مواقعي'],go:'Assets',icon:ScanLine},
 'Launch Guard':{eyebrow:['READ-ONLY LAUNCH REVIEW','مراجعة الإطلاق بدون تعديل'],headline:['Understand release evidence before deploying.','راجع أدلة الإطلاق قبل النشر.'],desc:['Review an authorized repository pull request and its reported checks. This does not merge, deploy or certify security.','راجع طلب الدمج واختباراته بموافقة صاحب المستودع. الأداة مش بتدمج أو تنشر أو تمنح شهادة أمان.'],action:['Code-assisted fixes','إصلاحات بمساعدة الكود'],go:'Remediation',icon:FileCheck2},
 'Evidence Vault':{eyebrow:['CONTROLLED EVIDENCE','حفظ الأدلة بأمان'],headline:['Keep your assessment evidence organized.','احتفظ بأدلة الفحص منظمة وقابلة للمراجعة.'],desc:['Review recorded assessment evidence, exports and authorized legal holds without guessing what was collected.','راجع أدلة الفحص المحفوظة وصدّرها وتحكم في حفظها بموافقة واضحة، من غير افتراض وجود أدلة غير مسجلة.'],action:['Assessment history','سجل الفحوص'],go:'Assessments',icon:LockKeyhole},
 'Agency':{eyebrow:['DELEGATED CLIENT ACCESS','صلاحيات العملاء المفوضة'],headline:['Manage client workspaces with explicit permission.','أدر حسابات عملائك بتفويض واضح.'],desc:['Client portfolio access, branded reporting and assessment permissions are separate. Clients must explicitly delegate each access.','إدارة المحافظ وتقارير العلامة التجارية والتصريح بالفحص صلاحيات منفصلة؛ لازم العميل يوافق على كل نوع وصول.'],action:['Team access','صلاحيات الفريق'],go:'Team',icon:Globe2},
 'Onboarding':{eyebrow:['CUSTOMER WORKFLOW','رحلة العميل'],headline:['Guide customers from invitation to verification.','ساعد العملاء من الدعوة حتى إثبات الملكية.'],desc:['Organize customer onboarding without enabling assessments or making changes before they approve.','نظّم تهيئة العميل من غير فحوص أو تعديل قبل موافقته الصريحة.'],action:['Website verification','إثبات ملكية المواقع'],go:'Assets',icon:BookOpen},
 'Team':{eyebrow:['ROLE-BASED ACCESS','صلاحيات حسب الدور'],headline:['The right access for the right people.','الصلاحية المناسبة للشخص المناسب.'],desc:['Review team invitations and access roles before delegating customer or security operations.','راجع الدعوات والصلاحيات قبل مشاركة بيانات العملاء أو عمليات الأمان.'],action:['Workspace overview','نظرة عامة'],go:'Overview',icon:Users},
 'Support':{eyebrow:['SECURE SUPPORT','الدعم الآمن'],headline:['Get help without exposing credentials.','اطلب المساعدة من غير مشاركة كلمات المرور.'],desc:['Keep support tickets and attachments organized in your workspace. Never share passwords or secret keys.','احتفظ بطلبات الدعم والمرفقات في مساحة العمل، وما تشاركش كلمات مرور أو مفاتيح سرية.'],action:['My findings','ملاحظات موقعي'],go:'Findings',icon:HelpCircle},
 'Account security':{eyebrow:['ACCOUNT PROTECTION','حماية الحساب'],headline:['Keep access to your workspace protected.','حافظ على أمان حسابك ومساحة عملك.'],desc:['Review sign-in settings, verification and MFA. These controls are separate from website ownership proof.','راجع تسجيل الدخول والتحقق والمصادقة الثنائية. حماية الحساب منفصلة عن إثبات ملكية المواقع.'],action:['Workspace overview','نظرة عامة'],go:'Overview',icon:Settings2},
};
export default function WorkspaceToolGuide({page,onNavigate}:{page:string;onNavigate:(page:string)=>void}){
 const {t}=useExperience();
 if(!(page in tools))return null;
 const item=tools[page as Tool],Icon=item.icon;
 return <section className="ops-hero ops-tool-intro" aria-label={t('Tool overview','نظرة على الأداة')}>
  <div className="ops-eyebrow"><Icon size={15}/>{t(...item.eyebrow)}</div>
  <div className="ops-hero-content"><div><h2>{t(...item.headline)}</h2><p>{t(...item.desc)}</p></div>
   <button type="button" onClick={()=>onNavigate(item.go)}>{t(...item.action)} <ArrowRight size={15}/></button>
  </div>
 </section>;
}
