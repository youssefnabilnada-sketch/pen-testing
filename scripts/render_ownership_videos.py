#!/usr/bin/env python3
"""Render separate Arabic/English narrated MP4 ownership explainers.
Do not use sample values as ownership proofs; real unique tokens come from AEGIS.
"""
from __future__ import annotations
import asyncio
import os
import subprocess
import tempfile
import logging
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


VOICE_CODES={"ar":"ar-EG-SalmaNeural","en":"en-US-JennyNeural"}
VOICE_FALLBACK={"ar":"ar","en":"en-us"}
EDGE_ENABLED={"ar":True,"en":True}

def duration(path:Path)->float:
    result=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
      "-of","default=noprint_wrappers=1:nokey=1",str(path)],check=True,
      capture_output=True,text=True)
    return float(result.stdout.strip())

async def _edge_voice(text:str,language:str,target:Path):
    import edge_tts
    await asyncio.wait_for(edge_tts.Communicate(text,voice=VOICE_CODES[language],rate="-5%").save(str(target)),timeout=25)

def speak(text:str,language:str,output:Path)->Path:
    """Use a natural neural voice when available; offline language-correct fallback."""
    if EDGE_ENABLED[language]:
        for attempt in range(3):
            try:
                output.unlink(missing_ok=True)
                asyncio.run(_edge_voice(text,language,output))
                if output.stat().st_size<1000 or duration(output)<0.5:
                    raise ValueError("TTS returned empty audio")
                return output
            except Exception as exc:
                if attempt<2:
                    import time
                    time.sleep(attempt+1)
                else:
                    EDGE_ENABLED[language]=False
                    logging.warning("Neural %s voice unavailable after retries (%s); using offline speech",language,type(exc).__name__)
    target=output.with_suffix(".wav")
    subprocess.run(["espeak-ng","-v",VOICE_FALLBACK[language],"-s",
                    "135" if language=="ar" else "145","-w",str(target),text],check=True)
    if duration(target)<0.5:raise RuntimeError("Offline narration missing")
    return target

def draw_slide(title:str,step:int,text:str,destination:Path,language:str):
    """One language per frame, with proper Arabic shaping and RTL alignment."""
    rtl=language=="ar"
    image=Image.new("RGB",SIZE)
    dr=ImageDraw.Draw(image)
    width,height=SIZE
    for y in range(height):
        dr.line((0,y,width,y),fill=(int(8+y*.008),int(18+y*.018),int(30+y*.02)))
    dr.ellipse((728,-170,1105,210),fill=(16,63,63))
    dr.ellipse((-140,310,185,690),fill=(17,41,64))
    dr.rounded_rectangle((39,35,922,504),radius=24,fill=(17,32,47),outline=(51,105,110),width=2)
    dr.rounded_rectangle((59,52,105,97),radius=12,fill=(39,126,112))
    dr.line((72,74,82,84,97,64),fill=CYAN,width=5)
    dr.text((117,60),"AEGIS",font=BRAND,fill=WHITE)
    label="دليل إثبات الملكية" if rtl else "SMARTVERIFY • OWNERSHIP TUTORIAL"
    dr.text((883 if rtl else 235,67),label,font=font("Noto Sans Arabic",21) if rtl else TINY,
            fill=MUTED,anchor="ra" if rtl else None,direction="rtl" if rtl else "ltr")
    dr.line((68,117,892,117),fill=(38,72,85),width=2)
    heading=ARABIC_TITLE if rtl else LATIN_TITLE
    heading_lines=wrapping(dr,title,heading,780,rtl)
    top=149
    for line in heading_lines:
        dr.text((880 if rtl else 79,top),line,font=heading,fill=WHITE,
                anchor="ra" if rtl else None,direction="rtl" if rtl else "ltr")
        top+=55
    num=f"الخطوة {step+1} من 3" if rtl else f"STEP {step+1} OF 3"
    numfont=ARABIC if rtl else LATIN_SMALL
    dr.text((875 if rtl else 81,top+23),num,font=numfont,fill=CYAN,
            anchor="ra" if rtl else None,direction="rtl" if rtl else "ltr")
    bodyfont=ARABIC if rtl else LATIN_SMALL
    y=max(323,top+73)
    bodylines=wrapping(dr,text,bodyfont,770,rtl)
    for line in bodylines:
        dr.text((875 if rtl else 82,y),line,font=bodyfont,fill=(206,237,230),
                anchor="ra" if rtl else None,direction="rtl" if rtl else "ltr")
        y+=41 if rtl else 35
    for k in range(3):
        dr.rounded_rectangle((74+280*k,473,334+280*k,479),radius=3,
                             fill=CYAN if k<=step else (55,76,91))
    disclaimer=("رسم توضيحي • رموز التحقق الحقيقية داخل حسابك فقط" if rtl else
                "ILLUSTRATION • ACTUAL PROOF TOKENS ARE INSIDE YOUR ACCOUNT")
    dr.text((880 if rtl else 79,513),disclaimer,font=font("Noto Sans Arabic",16) if rtl else TINY,
            fill=(137,165,172),anchor="ra" if rtl else None,direction="rtl" if rtl else "ltr")
    image.save(destination,optimize=True)

def vtt_timestamp(seconds:float)->str:
    milliseconds=round(seconds*1000)
    h,remaining=divmod(milliseconds,3600000)
    m,remaining=divmod(remaining,60000)
    s,ms=divmod(remaining,1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def make_video(slug:str,title:str,steps:list,language:str,work:Path):
    segments=[]
    cues=[]
    elapsed=0.0
    for index,(english,arabic) in enumerate(steps):
        narration=arabic if language=="ar" else english
        image=work/f"{slug}-{language}-{index}.png"
        draw_slide(title,index,narration,image,language)
        voice=speak(narration,language,work/f"{slug}-{language}-{index}.mp3")
        speaking=duration(voice)
        clip_duration=speaking+1.1
        clip=work/f"{slug}-{language}-{index}.mp4"
        subprocess.run([
          "ffmpeg","-y","-hide_banner","-loglevel","error",
          "-loop","1","-framerate","12","-i",str(image),"-i",str(voice),
          "-map","0:v:0","-map","1:a:0","-t",f"{clip_duration:.3f}",
          "-vf","fps=12,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","28",
          "-c:a","aac","-b:a","96k","-ar","44100","-ac","1",
          "-af","apad","-movflags","+faststart",str(clip)
        ],check=True)
        segments.append(clip)
        cues.append(f"{vtt_timestamp(elapsed)} --> {vtt_timestamp(elapsed+clip_duration)}\n{narration}\n")
        elapsed+=clip_duration
    manifest=work/f"{slug}-{language}-concat.txt"
    manifest.write_text("".join(f"file '{clip}'\n" for clip in segments),encoding="utf-8")
    output=OUT/f"{slug}-{language}.mp4"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
       "-f","concat","-safe","0","-i",str(manifest),"-c","copy",
       "-movflags","+faststart",str(output)],check=True)
    (OUT/f"{slug}-{language}.vtt").write_text("WEBVTT\n\n"+"\n".join(cues),encoding="utf-8")
    streams=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_type",
       "-of","csv=p=0",str(output)],capture_output=True,text=True,check=True).stdout.splitlines()
    if "audio" not in streams or "video" not in streams or output.stat().st_size<10000:
        raise RuntimeError(f"Expected a real narrated MP4 with video and audio: {output}")
    print(f"{slug}-{language}: narrated {duration(output):.1f}s, {output.stat().st_size} bytes",flush=True)

def render():
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aegis-voice-videos-") as name:
        work=Path(name)
        for slug,(english_title,arabic_title,steps) in METHODS.items():
            for language in ("ar","en"):
                make_video(slug,arabic_title if language=="ar" else english_title,
                           steps,language,work)
    # Old mixed-language files are intentionally removed only after both languages succeed.
    for slug in METHODS:
        old=OUT/f"{slug}.mp4"
        if old.exists():old.unlink()

if __name__=="__main__":
    render()
