'use client';
import {Info,ShieldCheck} from 'lucide-react';
import {useExperience} from './Experience';

type LanguagePair=[string,string];
type Guide={steps:[LanguagePair,LanguagePair,LanguagePair];disclaimer?:LanguagePair};
const guides:Record<string,Guide>={
 github:{steps:[
  ['Download the verification file or prepare it with the GitHub shortcut below.','نزّل ملف إثبات الملكية أو جهّزه باستخدام اختصار GitHub بالأسفل.'],
  ['Commit the file to the branch your actual website deploys from.','احفظ الملف على فرع GitHub الذي يُنشر منه موقعك الفعلي.'],
  ['Wait for deployment, then confirm ownership of the live website in AEGIS.','انتظر نشر الموقع، ثم تحقق من الملكية على الموقع المنشور داخل AEGIS.']
 ],disclaimer:['Repository ownership alone cannot verify a website.','ملكية المستودع وحدها لا تثبت التحكم في الموقع.']},
 vercel:{steps:[
  ['Download the proof file and add it to the public/.well-known folder of your website project.','نزّل ملف الإثبات وضعه في مجلد public/.well-known بمشروع موقعك.'],
  ['Deploy to the exact Vercel domain you registered with AEGIS.','انشر على نفس عنوان Vercel الذي سجلته في AEGIS.'],
  ['Confirm the file is publicly accessible, then verify here.','تأكد أن رابط الملف متاح على الموقع ثم تحقق هنا.']
 ],disclaimer:['This is a guided file setup, not a direct Vercel account connection.','هذه خطوات لإعداد ملف الإثبات وليست ربطًا مباشرًا بحساب Vercel.']},
 wordpress:{steps:[
  ['Open your WordPress administrator dashboard.','افتح لوحة تحكم مدير WordPress.'],
  ['Add the exact AEGIS meta tag with a trusted header or SEO plugin, or use the AEGIS WordPress verification helper below.','أضف وسم AEGIS عبر إضافة موثوقة للترويسة أو SEO، أو استخدم مساعدة WordPress الموجودة بالأسفل.'],
  ['Publish, clear your site cache and check ownership.','انشر التعديل وامسح ذاكرة التخزين المؤقت ثم تحقق من الملكية.']
 ]},
 shopify:{steps:[
  ['Open the published theme in your Shopify Online Store settings.','افتح القالب المنشور من إعدادات المتجر في Shopify.'],
  ['If permitted, add the exact AEGIS meta tag inside the HTML head and save.','إذا كانت صلاحياتك تسمح، أضف وسم AEGIS داخل head بقالب المتجر ثم احفظ.'],
  ['Check the public storefront contains the tag and verify ownership here.','تأكد أن الوسم ظاهر في المتجر العام ثم تحقق هنا.']
 ],disclaimer:['Theme editing permissions are needed. Otherwise choose DNS TXT under other methods.','تحتاج صلاحية تعديل القالب، وإلا اختر سجل DNS TXT من الطرق الأخرى.']},
 wix:{steps:[
  ['Open your Wix dashboard and find the DNS settings for the custom domain you control.','افتح لوحة Wix وإعدادات DNS للدومين المخصص الذي تتحكم فيه.'],
  ['Create the unique AEGIS TXT record shown in the next step.','أضف سجل TXT الفريد الذي يعرضه AEGIS في الخطوة التالية.'],
  ['Allow DNS propagation, then confirm ownership.','انتظر انتشار سجل DNS ثم تحقق من الملكية.']
 ],disclaimer:['DNS proof requires control of the domain. A Wix subdomain may need a different method.','إثبات DNS يتطلب التحكم بالدومين. مواقع Wix ذات النطاق الفرعي قد تحتاج طريقة مختلفة.']},
 squarespace:{steps:[
  ['Open your custom-domain DNS management settings.','افتح إعدادات إدارة DNS لدومينك المخصص.'],
  ['Publish the exact AEGIS TXT record shown after choosing this method.','انشر سجل AEGIS TXT المحدد بعد اختيار الطريقة.'],
  ['Wait for propagation and run the ownership check.','انتظر انتشار السجل ثم نفذ التحقق من الملكية.']
 ],disclaimer:['Only domains you can manage in DNS are eligible for this method.','هذه الطريقة متاحة للدومينات التي تستطيع إدارة سجلات DNS الخاصة بها.']},
 cloudflare:{steps:[
  ['Open the DNS zone for the domain you registered.','افتح إعدادات DNS للدومين المسجل في AEGIS.'],
  ['Add the displayed AEGIS TXT record, or explicitly approve the one-record Cloudflare assistance below.','أضف سجل AEGIS TXT المعروض، أو وافق صراحة على مساعدة Cloudflare لنشر سجل واحد فقط بالأسفل.'],
  ['Wait for DNS propagation, then confirm ownership separately.','انتظر انتشار السجل ثم تحقق من الملكية بشكل منفصل.']
 ],disclaimer:['The assisted option never grants scanning rights and requires a restricted token.','خيار المساعدة لا يمنح صلاحية الفحص ويتطلب رمز وصول محدود الصلاحيات.']},
 cpanel:{steps:[
  ['Open the file manager for your actual site in cPanel or Plesk.','افتح مدير ملفات الموقع الفعلي في cPanel أو Plesk.'],
  ['Upload the downloaded proof under .well-known in the site document root.','ارفع ملف الإثبات داخل .well-known في المجلد العام للموقع.'],
  ['Confirm the file URL is publicly accessible and verify it here.','تأكد من فتح رابط الملف للعامة ثم تحقق منه هنا.']
 ]},
 netlify:{steps:[
  ['Download the AEGIS file and add it to your deployed public output under .well-known.','نزّل ملف AEGIS وضعه داخل .well-known في ملفات الموقع المنشورة.'],
  ['Publish the updated site to the exact Netlify address registered here.','انشر الموقع المحدث على نفس عنوان Netlify المسجل هنا.'],
  ['Check that the public proof URL works, then confirm ownership.','تأكد أن رابط الإثبات العام يعمل ثم تحقق من الملكية.']
 ]},
 google:{steps:[
  ['Google Search Console verification does not automatically prove ownership to AEGIS.','إثبات ملكية Google Search Console لا يعني إثبات الملكية في AEGIS تلقائيًا.'],
  ['Use your control of the domain DNS to publish the unique AEGIS TXT record.','استخدم صلاحيتك في إدارة DNS لإضافة سجل AEGIS TXT الفريد.'],
  ['Wait for propagation and verify the domain in AEGIS.','انتظر انتشار سجل DNS ثم تحقق من الدومين في AEGIS.']
 ],disclaimer:['Direct Google Search Console authorization is not connected yet. Never share your Google password.','الربط المباشر مع Google Search Console غير مفعل بعد. لا تشارك كلمة مرور Google.']},
 unsure:{steps:[
  ['You do not need GitHub or specialist technical knowledge to begin.','مش محتاج GitHub أو خبرة تقنية متخصصة علشان تبدأ.'],
  ['Use DNS TXT if you manage the domain, or choose HTML File / Meta Tag from the other methods below.','استخدم DNS TXT لو بتدير الدومين، أو اختار ملف HTML أو Meta Tag من الطرق الأخرى بالأسفل.'],
  ['Publish the proof on the exact website and confirm ownership.','انشر الإثبات على نفس الموقع المطلوب ثم تحقق من الملكية.']
 ]}
};
export default function SmartVerifyPlatformGuide({platform}:{platform:string}){
 const {t}=useExperience();
 const guide=guides[platform]||guides.unsure;
 return <aside className="ownership-platform-guide" aria-label={t('Platform setup guide','دليل إعداد المنصة')}>
  <div className="ownership-platform-guide-title"><ShieldCheck size={17} aria-hidden="true"/><strong>{t('The shortest verified path for your website','أقصر طريقة آمنة لإثبات ملكية موقعك')}</strong><span>{t('Guided setup','إعداد موجه')}</span></div>
  <ol>{guide.steps.map(([en,ar])=><li key={en}>{t(en,ar)}</li>)}</ol>
  {guide.disclaimer&&<p className="ownership-platform-warning"><Info size={15} aria-hidden="true"/>{t(...guide.disclaimer)}</p>}
  <small>{t('AEGIS checks the published website, not merely your login to its hosting or repository provider. Verification never starts an assessment.','AEGIS بيتحقق من الموقع المنشور نفسه، وليس فقط من تسجيل دخولك للاستضافة أو GitHub. إثبات الملكية لا يبدأ الفحص.')}</small>
 </aside>;
}
