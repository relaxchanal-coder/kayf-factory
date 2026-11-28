# معلومات الأرض — مصنع الفيديو (فرع ard)

قناة «معلومات الأرض» (UCTE7xT3ojth4Si0JyE-5kfQ): تقارير عربية فصحى بأسلوب Vox — خرائط ورسوم ورقية.
الجدول: فيديو طويل 8–10 دقائق الأحد والأربعاء والجمعة 6:00 م (بغداد)، وشورتان تشويقيان من كل فيديو
يُنشران في الأيام بينها 6:00 م، وكل شورت يُربط بالفيديو الطويل عبر «الفيديو ذو الصلة».

## خطوات حلقة جديدة
1. ابحث عن موضوع قوي الطلب ومناسب للمعلنين (لا مشاهد عنيفة، حياد سياسي، لا وجوه أشخاص حقيقيين).
2. اكتب السكربت مقاطع قصيرة (جملة أو جملتان) في `ard/tts/<id>.json` (≈ 1,000 كلمة لثماني دقائق ونصف،
   الأرقام بالحروف). ادفع إلى فرع `ard` → يشغّل `ard-tts.yml` صوت مايكروسوفت (ar-SA-HamedNeural)
   ويضع `seg_XX.mp3` و `timings.json` في فرع `ard-audio/<id>/`.
3. ارسم المشاهد بمكتبة `ard/engine` (engine.py: الورق، البطاقات، التظليل الأصفر، الكاميرا؛ scenes.py: tag/pin/T…)
   وخرائط `mapr.py` (منطقة قابلة للتعديل) — انظر `ard/episodes/001-iran-iraq` مثالاً كاملاً.
   غيّر الألوان والشكل في كل حلقة (سياسة يوتيوب ضد المحتوى المتكرر).
4. `render_ii.py video|audio|mux` ثم `shorts_ii.py` و `thumb.py`. الفيديو الطويل يجب أن يبقى < 95MB.
5. ارفع الملفات إلى فرع `ard-videos` مع `manifest.json` (title, description, tags, publish_at, file, thumb, related).

متطلبات: ffmpeg، Pillow مع raqm، numpy، node + world-atlas + topojson-client، خطوط Cairo/IBM Plex Sans Arabic/Oswald
(من github.com/google/fonts).
