# Custom logging level
PRD_INFO = 41
LEVEL_PRD_INFO = 'PRD_INFO'

# Number of seconds in a day
DAY_SECS = 86399
ONE_TIME_LINK_MAX_AGE = 172800
TWILIO_TOKEN_URL_SENDER = 'f'
TWILIO_TOKEN_URL_RECIPIENT = 't'
TWILIO_TOKEN_PARAM_PKEY = 'personalized_key'
TWILIO_TOKEN_PARAM_REV_DT = 'revocation_date_time'
TOKEN_URL_SMS_MSG_BODY_TEMPLATE = 'You have a new message from {}. Click the link below to read and reply:\n{}'

# Date constants
ONE_WEEK = '1-week'
ONE_MONTH = '1-month'
THREE_MONTH = '3-month'
SIX_MONTH = '6-month'
ONE_YEAR = '1-year'
TIME_PERIODS = {ONE_WEEK: 7, ONE_MONTH: 30, THREE_MONTH: 91, SIX_MONTH: 183, ONE_YEAR: 365}

US_DATE_FMT = '%m/%d/%Y'
US_TIME_FMT = '%I:%M %p'
US_DATETIME_FMT = US_DATE_FMT + ' ' + US_TIME_FMT
ISO_DATE_FMT = '%Y-%m-%d'
ISO_TIME_FMT = '%H:%M'
ISO_DATETIME_FMT = ISO_DATE_FMT + ' ' + ISO_TIME_FMT
ISO_DATETIME_TZ_FMT = '%Y-%m-%dT%H:%M:%S%z'


# Encrypted file/image fields path
ENC_PATH_USER_PROFILE_IMAGE = 'img/profile/'


# API display names
ASTHMAMD = 'AsthmaMD'
BODIMETRICS = 'BodiMetrics'
EMFIT = 'Emfit'
FITBIT = 'Fitbit'
GARMIN = 'Garmin'
IGLUCOSE = 'iGlucose'
IHEALTH = 'iHealth'
MYFITNESSPAL = 'MyFitnessPal'
OMRON = 'Omron'
PEAR = 'PearSports'
POLAR = 'Polar'
STRAVA = 'Strava'
STRIIV = 'Striiv'
SUUNTO = 'Suunto'
TELCARE = 'Telcare'
UA = 'UnderArmour'
WITHINGS = 'Withings'
YOO = 'Yoo'
DEXCOM = 'Dexcom'
SMARTTHINGS = 'Samsung SmartThings'
MY_MOJO_HEALTH = 'Keto-Mojo'

# Fitbit Data Types
FB_DTYPE_ACTIVITIES = 'activities'
FB_DTYPE_FOODS = 'foods'
FB_DTYPE_BODY = 'body'
FB_DTYPE_SLEEP = 'sleep'

# Fitbit Heart Rate Intraday Detail Levels
FB_HR_LEVEL_1SEC = '1sec'
FB_HR_LEVEL_1MIN = '1min'

# Fitbit Scopes
FB_SCOPE_SETTINGS = 'settings'
FB_SCOPE_SLEEP = 'sleep'
FB_SCOPE_ACTIVITY = 'activity'
FB_SCOPE_PROFILE = 'profile'
FB_SCOPE_LOCATION = 'location'
FB_SCOPE_NUTRITION = 'nutrition'
FB_SCOPE_WEIGHT = 'weight'
FB_SCOPE_HEART_RATE = 'heartrate'
FB_SCOPE_SOCIAL = 'social'

# Garmin summary resources
GS_DAILIES = 'dailies'
GS_3RD_PARTY_DAILIES = 'thirdPartyDailies'
GS_ACTIVITIES = 'activities'
GS_MANUAL_ACTIVITIES = 'manuallyUpdatedActivities'
GS_ACT_DETAILS = 'activityDetails'
GS_EPOCHS = 'epochs'
GS_SLEEPS = 'sleeps'
GS_BODY_COMPS = 'bodyComps'
GS_STRESS_DETAILS = 'stressDetails'
GS_USER_METRICS = 'userMetrics'
GS_MOVE_IQ = 'moveiq'
GS_PULSE_OX = 'pulseOx'
GS_RESPIRATION = 'respiration'

# Garmin Backfill request rate limit time interval in seconds (1 minute + 5s buffer)
GS_BACKFILL_TIME_INTERVAL = 60
GS_BACKFILL_REQ_BUFFER = 5

# Dexcom API models
DEXCOM_CALIBRATION = 'DexcomCalibration'
DEXCOM_DATARANGE = 'DexcomDataRange'
DEXCOM_DEVICE = 'DexcomDevice'
DEXCOM_DEVICE_ALERTSCHEDULE = 'DexcomDeviceAlertSchedule'
DEXCOM_DEVICE_ALERTSETTING = 'DexcomDeviceAlertSetting'
DEXCOM_EGV = 'DexcomEgv'
DEXCOM_EVENT = 'DexcomEvent'

# Polar Resources
POLAR_SLEEP = 'sleep'
POLAR_ACTIVITY = 'daily_activity'
POLAR_TRAINING = 'training_data'
POLAR_PHYSICAL_INFO = 'physical_info'

# HTTP status code
CODE_NO_CONTENT = 204
CODE_BAD_REQUEST = 400
CODE_FORBIDDEN = 403
