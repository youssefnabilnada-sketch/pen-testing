#!/usr/bin/env python3
"""Render original silent bilingual MP4 explainers. No logos/screenshots of third parties.
Do not use sample values as ownership proofs; real unique tokens come from AEGIS.
"""
from __future__ import annotations
import os
import subprocess
import tempfile
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"apps/web/public/guides/videos"
SIZE=(960,540)
CYAN=(108,231,210)
WHITE=(242,252,250)
MUTED=(167,194,207)
METHODS={
 "file":("HTML Verification File","ملف إثبات الملكية",
  [("Download your unique AEGIS proof file.","نزّل ملف الإثبات المخصص من AEGIS."),
   ("Upload it unchanged to your website's public .well-known folder.","ارفعه بدون تعديل داخل مجلد .well-known العام في موقعك."),
   ("Open the file URL and click Check ownership.","افتح رابط الملف واضغط تحقق من الملكية.")]),
 "dns":("DNS TXT Record","سجل DNS TXT",
  [("Copy the unique TXT record name and value from AEGIS.","انسخ اسم وقيمة سجل TXT المخصص من AEGIS."),
   ("Add the record to your domain's DNS settings.","أضف السجل إلى إعدادات DNS للدومين الخاص بك."),
   ("Allow propagation, then verify in AEGIS.","انتظر انتشار DNS ثم تحقق من الملكية في AEGIS.")]),
 "meta":("HTML Meta Tag","وسم Meta Tag",
  [("Copy your website's unique AEGIS meta tag.","انسخ وسم التحقق الفريد من AEGIS."),
   ("Paste it in your published homepage HTML head.","ضع الوسم في رأس الصفحة الرئيسية المنشورة بموقعك."),
   ("Save, clear your cache, then check ownership.","احفظ التعديلات وامسح الكاش ثم تحقق من الملكية.")]),
 "wordpress":("WordPress","ووردبريس",
  [("Open your WordPress dashboard.","افتح لوحة تحكم WordPress."),
   ("Add the AEGIS meta tag using a trusted header or SEO plugin.","أضف وسم AEGIS باستخدام إضافة ترويسة أو SEO موثوقة."),
   ("Publish, clear the cache, and verify.","انشر التعديل وامسح الكاش ثم تحقق من الملكية.")]),
 "shopify":("Shopify","شوبيفاي",
  [("Open your published Shopify storefront theme.","افتح قالب متجر Shopify المنشور."),
   ("With theme access, place the AEGIS meta tag inside HTML head.","لو معاك صلاحية التعديل، ضع وسم AEGIS داخل head."),
   ("Save the theme and check the published store.","احفظ القالب ثم تحقق من المتجر المنشور.")]),
 "wix":("Wix","ويكس",
  [("Open the DNS panel for your Wix custom domain.","افتح إعدادات DNS للدومين المخصص على Wix."),
   ("Create the AEGIS TXT record using its exact name and value.","أضف سجل AEGIS TXT بالاسم والقيمة المعروضين."),
   ("After DNS propagation, confirm ownership in AEGIS.","بعد انتشار سجل DNS، تحقق من الملكية في AEGIS.")]),
 "squarespace":("Squarespace","سكوير سبيس",
  [("Open DNS settings for the custom domain you manage.","افتح إعدادات DNS للدومين المخصص الذي تديره."),
   ("Publish your unique AEGIS TXT verification record.","انشر سجل AEGIS TXT الفريد لإثبات الملكية."),
   ("Check propagation and confirm the exact domain.","تحقق من انتشار السجل وملكية نفس الدومين.")]),
 "cloudflare":("Cloudflare","كلاودفلير",
  [("Open the DNS zone for your registered website.","افتح إعدادات DNS للموقع المسجل."),
   ("Add AEGIS TXT manually or approve its restricted one-record helper.","أضف سجل AEGIS TXT أو وافق على المساعدة المحدودة بسجل واحد."),
   ("Verify the published record. Scanning requires separate consent.","تحقق من السجل المنشور؛ الفحص يتطلب موافقة منفصلة.")]),
 "vercel":("Vercel","فيرسل",
  [("Download the AEGIS HTML verification file.","نزّل ملف إثبات الملكية من AEGIS."),
   ("Place it under public/.well-known in your website project.","ضعه داخل public/.well-known في مشروع موقعك."),
   ("Deploy to the exact website URL and confirm ownership.","انشره على نفس عنوان موقعك ثم تحقق من الملكية.")]),
 "netlify":("Netlify","نتليفاي",
  [("Download the unique AEGIS proof file.","نزّل ملف AEGIS الفريد لإثبات الملكية."),
   ("Add it to .well-known inside your published site's output.","ضعه داخل .well-known في ملفات الموقع المنشورة."),
   ("Deploy, open the file URL, and verify.","انشر الموقع وافتح رابط الملف ثم تحقق من الملكية.")]),
 "github":("GitHub Pages / Git","GitHub Pages / Git",
  [("Download the AEGIS proof file or use the Git helper.","نزّل ملف AEGIS أو استخدم مساعدة Git."),
   ("Commit the file and deploy the real website.","احفظ الملف في المستودع ثم انشر موقعك الحقيقي."),
   ("AEGIS checks the live website, not the repository account.","AEGIS يتحقق من الموقع المنشور، وليس حساب المستودع.")]),
 "cpanel":("cPanel / Plesk","سي بانل / بليسك",
  [("Open your website's hosting file manager.","افتح مدير الملفات في استضافة موقعك."),
   ("Upload the AEGIS proof to the public .well-known directory.","ارفع ملف AEGIS إلى مجلد .well-known العام."),
   ("Check the public file URL and verify ownership.","تأكد من رابط الملف العام ثم تحقق من الملكية.")]),
 "google":("Google Search Console","جوجل سيرش كونسول",
  [("Google verification alone does not verify ownership to AEGIS.","التحقق في Google وحده لا يثبت الملكية لدى AEGIS."),
   ("Add the unique AEGIS DNS TXT record to your domain.","أضف سجل AEGIS DNS TXT الفريد إلى دومينك."),
   ("Wait for the record and verify directly inside AEGIS.","انتظر السجل ثم تحقق من الملكية داخل AEGIS.")]),
 "unsure":("Any website / Custom","أي موقع / مخصص",
  [("Enter the exact website you control in AEGIS.","أدخل عنوان الموقع الذي تتحكم فيه في AEGIS."),
   ("Choose file, meta tag or DNS based on your available access.","اختر ملف HTML أو Meta Tag أو DNS حسب صلاحيتك."),
   ("Publish the real proof and check ownership.","انشر الإثبات الحقيقي ثم تحقق من الملكية.")]),
}

def font(family:str, size:int):
    matched=subprocess.check_output(["fc-match","-f","%{file}",family],text=True).strip()
    return ImageFont.truetype(matched,size,layout_engine=ImageFont.Layout.RAQM)

LATIN=font("DejaVu Sans",33)
LATIN_SMALL=font("DejaVu Sans",22)
LATIN_TITLE=font("DejaVu Sans:style=Bold",46)
ARABIC=font("Noto Sans Arabic",29)
ARABIC_TITLE=font("Noto Sans Arabic",40)
BRAND=font("DejaVu Sans:style=Bold",24)
TINY=font("DejaVu Sans",15)

def wrapping(draw, text, font_, max_px, rtl=False):
    words=text.split()
    lines=[]
    current=""
    for word in words:
        trial=(current+" "+word).strip()
        if draw.textbbox((0,0),trial,font=font_,direction="rtl" if rtl else "ltr")[2] > max_px and current:
            lines.append(current)
            current=word
        else:current=trial
    if current:lines.append(current)
    return lines

def draw_slide(topic,arabic,step_number,eng,ar,out):
    im=Image.new("RGB",SIZE)
    dr=ImageDraw.Draw(im)
    w,h=SIZE
    for y in range(h):
        dr.line((0,y,w,y),fill=(int(8+y*.008),int(18+y*.018),int(30+y*.021)))
    dr.ellipse((725,-170,1100,205),fill=(16,62,65))
    dr.ellipse((-130,300,180,660),fill=(16,39,65))
    dr.rounded_rectangle((42,38,918,502),radius=24,fill=(17,32,47),outline=(51,99,105),width=2)
    dr.rounded_rectangle((60,53,104,96),radius=12,fill=(40,123,114))
    dr.line((72,71,82,82,95,65),fill=CYAN,width=5)
    dr.text((118,61),"AEGIS",font=BRAND,fill=WHITE)
    dr.text((228,67),"SMARTVERIFY  /  VIDEO TUTORIAL",font=TINY,fill=MUTED)
    dr.text((865,73),f"{step_number+1} / 3",font=LATIN_SMALL,fill=CYAN,anchor="ra")
    dr.line((68,117,892,117),fill=(39,67,81),width=2)
    dr.text((80,144),topic,font=LATIN_TITLE,fill=WHITE)
    dr.text((878,227),arabic,font=ARABIC_TITLE,fill=CYAN,anchor="ra",direction="rtl")
    dr.text((80,259),f"STEP {step_number+1:02d}",font=LATIN_SMALL,fill=CYAN)
    line_y=304
    for line in wrapping(dr,eng,LATIN_SMALL,800):
        dr.text((80,line_y),line,font=LATIN_SMALL,fill=WHITE)
        line_y+=34
    line_y=max(382,line_y+24)
    for line in wrapping(dr,ar,ARABIC,800,True):
        dr.text((880,line_y),line,font=ARABIC,fill=(193,233,225),anchor="ra",direction="rtl")
        line_y+=40
    for k in range(3):
        rect=(74+280*k,473,334+280*k,479)
        dr.rounded_rectangle(rect,radius=3,fill=CYAN if k<=step_number else (55,76,91))
    dr.text((78,510),"ILLUSTRATION • NO REAL ACCOUNTS OR PROOF TOKENS • NO AUTO SCAN",font=TINY,fill=(118,150,162))
    im.save(out,optimize=True)

def render():
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aegis-videos-") as tmp:
        work=Path(tmp)
        for slug,(topic,arabic,steps) in METHODS.items():
            clips=[]
            for i,(en,ar) in enumerate(steps):
                p=work/f"{slug}-{i}.png"
                draw_slide(topic,arabic,i,en,ar,p)
                clips.append(p)
            manifest=work/f"{slug}.txt"
            # Concat demuxer respects duration for each still image.
            manifest.write_text("".join(f"file '{p}'\nduration 2.8\n" for p in clips)+f"file '{clips[-1]}'\n",encoding="utf-8")
            dest=OUT/(slug+".mp4")
            subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(manifest),"-vf","fps=15,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","27","-movflags","+faststart","-an",str(dest)],check=True)
            if dest.stat().st_size < 2000:raise RuntimeError(f"Empty MP4: {dest}")
            print(f"{slug}: {dest.stat().st_size} bytes")

if __name__=="__main__":
    render()
