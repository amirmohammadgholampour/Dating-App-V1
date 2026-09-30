# راهنمای احراز هویت و پروفایل کاربران

## اجرای تغییرات دیتابیس

پس از دریافت تغییرات، migration را روی محیط خود اجرا کنید:

```powershell
python manage.py migrate users
```

## احراز هویت با ایمیل و رمز عبور

- `POST /api/users/auth/register/email/` — بدنه شامل `email` و `password` (حداقل ۸ نویسه)؛ پاسخ موفق `201` و توکن‌های JWT.
- `POST /api/users/auth/login/email/` — بدنه شامل `email` و `password`؛ پاسخ موفق `200` و توکن‌های JWT.

ثبت‌نام و ورود دو مسیر جدا دارند. رمز عبور فقط هش‌شده در Django ذخیره می‌شود.

## احراز هویت با تلفن و کد یک‌بارمصرف

- `POST /api/users/auth/register/phone/request-code/` با `{"phone_number":"09123456789"}`
- `POST /api/users/auth/register/phone/verify-code/` با `{"phone_number":"09123456789","code":"123456"}`
- `POST /api/users/auth/login/phone/request-code/` با `{"phone_number":"09123456789"}`
- `POST /api/users/auth/login/phone/verify-code/` با `{"phone_number":"09123456789","code":"123456"}`

کد ۶ رقمی پس از ۵ دقیقه منقضی می‌شود، حداکثر ۵ بار قابل‌آزمایش است و فقط digest وابسته به `SECRET_KEY` در دیتابیس می‌ماند. درخواست کد برای هر شماره و روش در بازهٔ ۶۰ ثانیه یک بار پذیرفته می‌شود؛ پاسخ درخواست کد برای شماره‌های موجود و ناموجود یکسان است. محدودیت نرخ IP نیز اعمال شده است.

### اتصال سرویس پیامک

پروژه ارائه‌دهندهٔ پیامک ندارد. برای فعال‌کردن OTP، این مقادیر را در `.env.local` قرار دهید:

```dotenv
SMS_PROVIDER_URL=https://sms-provider.example/api/messages
SMS_PROVIDER_TOKEN=your-provider-token
```

`SMS_PROVIDER_URL` باید یک webhook HTTPS باشد که درخواست `POST` با JSON زیر را بپذیرد و با وضعیت HTTP موفق پاسخ دهد:

```json
{"phone_number":"09123456789","message":"Your verification code is 123456. It expires in 5 minutes."}
```

اگر token تنظیم شده باشد، درخواست هدر `Authorization: Bearer <token>` هم دارد. تا پیش از تنظیم این اتصال، endpoint درخواست OTP پاسخ `503` می‌دهد؛ کد به کلاینت برگردانده یا در لاگ ثبت نمی‌شود. درگاه واقعی باید شماره را به قالب موردنیاز خودش تبدیل کند، HTTPS داشته باشد و خطاهای ارسال را با پاسخ غیرموفق اعلام کند.

## تکمیل و مشاهدهٔ پروفایل

`PATCH /api/users/update/` با JWT می‌تواند `first_name`، `last_name`، `date_of_birth`، `province`، `city`، `bio`، `profile_picture`، `gender` و `interests` را دریافت کند. برای عکس، درخواست را به‌صورت `multipart/form-data` بفرستید. استان و شهر از شناسهٔ رکوردهای موجود ارسال می‌شوند.

`age` از روی `date_of_birth` هنگام ذخیرهٔ کاربر محاسبه و در دیتابیس نگهداری می‌شود؛ این فیلد از API قابل‌نوشتن نیست. `GET /api/users/profile/` و کارت‌های Discover آن را برمی‌گردانند.

## وضعیت آنلاین

کلاینتِ واردشده باید در زمان فعال‌بودن برنامه هر ۶۰ ثانیه `POST /api/users/presence/heartbeat/` را با JWT فراخوانی کند. کاربر تا ۵ دقیقه بعد از آخرین heartbeat آنلاین محسوب می‌شود. API پروفایل و کارت‌های Discover مقدار `is_online` را برمی‌گردانند. بدون heartbeat از سمت کلاینت، وضعیت آنلاین قابل‌به‌روزرسانی نیست.
