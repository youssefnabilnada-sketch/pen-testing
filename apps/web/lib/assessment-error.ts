/** Public-only failure messages. Historical jobs may lack a specific error code. */
type Translate=(english:string,arabic:string)=>string;

export function assessmentFailureText(raw:string|null|undefined,t:Translate):string {
 if(!raw)return t('Assessment did not finish; no result was verified.','لم يكتمل التقييم ولم يتم التحقق من أي نتيجة.');
 const status=/^The website returned HTTP (\d{3})\b/.exec(raw);
 if(status){
  const code=status[1];
  if(code==='401'||code==='403')return t(
   `The website returned HTTP ${code} (access restricted). Check whether the approved page is publicly accessible. Do not disable security protections for a scan; no assessment result was produced.`,
   `الموقع أعاد HTTP ${code} (الوصول مقيّد). تأكد من إتاحة الصفحة المصرّح بها بشكل مناسب، ولا تعطّل حماية الموقع لإجراء الفحص. لم تنتج أي نتيجة تقييم.`);
  if(code==='429')return t(
   'The website is rate-limiting requests (HTTP 429). Review its access policy and retry later with valid authorization. No assessment result was produced.',
   'الموقع يحدّ الطلبات (HTTP 429). راجع سياسة الوصول ثم حاول لاحقًا بتصريح صالح. لم تنتج أي نتيجة تقييم.');
  if(code.startsWith('5'))return t(
   `The website returned a server error (HTTP ${code}). Check the website service before retrying. No assessment result was produced.`,
   `الموقع أعاد خطأ في الخادم (HTTP ${code}). راجع حالة الموقع قبل إعادة الفحص. لم تنتج أي نتيجة تقييم.`);
  return t(
   `The website returned HTTP ${code} instead of a successful response. Confirm the authorized page is accessible. No assessment result was produced.`,
   `الموقع أعاد HTTP ${code} بدلًا من استجابة ناجحة. تأكد أن الصفحة المصرح بفحصها متاحة. لم تنتج أي نتيجة تقييم.`);
 }
 const known:[string,string,string][]=[
  ['The website redirected','The website redirected the request. AEGIS does not automatically follow redirects. Verify the final website address as a separate approved asset before retrying. No assessment result was produced.','الموقع حوّل الطلب إلى عنوان آخر. AEGIS لا تتبع التحويلات تلقائيًا. أثبت ملكية العنوان النهائي وصرّح بفحصه بصورة منفصلة قبل المحاولة. لم تنتج أي نتيجة تقييم.'],
  ['The website hostname could not','The scanner could not resolve the website DNS. Check public DNS configuration. No assessment result was produced.','تعذر على الفاحص الوصول إلى اسم الموقع عبر DNS. راجع إعدادات DNS العامة. لم تنتج أي نتيجة تقييم.'],
  ['The website resolved to','The website resolves outside the supported public assessment scope. Check its authorized address. No assessment result was produced.','عنوان الموقع خارج النطاق العام المسموح بفحصه. راجع العنوان المصرح به. لم تنتج أي نتيجة تقييم.'],
  ['The scanner could not establish','A valid HTTPS connection could not be established. Check the website certificate and TLS settings. No assessment result was produced.','تعذر إنشاء اتصال HTTPS صالح. راجع شهادة الموقع وإعدادات TLS. لم تنتج أي نتيجة تقييم.'],
  ['The website did not respond','The website did not respond within the authorized time limit. Check availability and try again. No assessment result was produced.','الموقع لم يستجب خلال المهلة المصرح بها. راجع حالة الموقع ثم حاول مجددًا. لم تنتج أي نتيجة تقييم.'],
  ['The scanner could not complete','The scanner could not connect to the website. Check availability and try again. No assessment result was produced.','تعذر على الفاحص الاتصال بالموقع. تأكد من إتاحته ثم حاول مجددًا. لم تنتج أي نتيجة تقييم.'],
  ['An assessment of this website','A scan started too recently. Wait at least one minute and begin a new authorized assessment. No result was produced.','تم بدء فحص لهذا الموقع مؤخرًا. انتظر دقيقة على الأقل ثم ابدأ فحصًا جديدًا بتصريح. لم تنتج أي نتيجة.'],
  ['The assessment authorization expired','Authorization expired or was outside its approved window. Review and approve a new assessment. No result was produced.','انتهى تصريح الفحص أو كان خارج وقته المحدد. راجع ووافق على فحص جديد. لم تنتج أي نتيجة.'],
  ['The assessment scope changed','The approved assessment scope changed. Review and authorize a new assessment. No result was produced.','تغير نطاق الفحص المعتمد. راجع النطاق وصرّح بفحص جديد. لم تنتج أي نتيجة.'],
  ['The assessment was stopped by','The assessment was stopped by a safety check. Review the exact website address and approved scope. No result was produced.','أوقف التقييم أحد ضوابط السلامة. راجع عنوان الموقع ونطاق الفحص المعتمد. لم تنتج أي نتيجة.'],
  ['The assessment could not finish','The assessment could not finish because of a processing issue. Contact support and provide the displayed job reference. No result was verified.','لم يكتمل التقييم بسبب مشكلة معالجة. تواصل مع الدعم واذكر مرجع المهمة الظاهر. لم يتم التحقق من أي نتيجة.'],
 ];
 const match=known.find(([prefix])=>raw.startsWith(prefix));
 if(match)return t(match[1],match[2]);
 return t(
  'This assessment failed. An earlier job may not have recorded its exact cause. Contact support with the job reference; no result was verified.',
  'فشل هذا الفحص، وربما لم يسجّل الإصدار السابق السبب الدقيق. تواصل مع الدعم مع ذكر مرجع المهمة؛ ولم يتم التحقق من أي نتيجة.'
 );
}
