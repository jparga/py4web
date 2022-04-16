"""
This file defines cache, session, and translator T object for the app
These are fixtures that every app needs so probably you will not be editing this file
"""
import copy
import sys
import logging
from py4web import Session, Cache, Translator, Flash, DAL, Field, action
from py4web.utils.mailer import Mailer
from py4web.utils.auth import Auth
from py4web.utils.factories import Inject
from py4web.utils.downloader import downloader
from pydal.tools.tags import Tags
from py4web.utils.factories import ActionFactory
from . import settings

# #######################################################
# implement custom loggers form settings.LOGGERS
# #######################################################
logger = logging.getLogger("py4web:" + settings.APP_NAME)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
for item in settings.LOGGERS:
    level, filename = item.split(":", 1)
    if filename in ("stdout", "stderr"):
        handler = logging.StreamHandler(getattr(sys, filename))
    else:
        handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)
    logger.setLevel(getattr(logging, level.upper(), "DEBUG"))
    logger.addHandler(handler)

# #######################################################
# connect to db
# #######################################################
db = DAL(
    settings.DB_URI,
    folder=settings.DB_FOLDER,
    pool_size=settings.DB_POOL_SIZE,
    migrate=settings.DB_MIGRATE,
    fake_migrate=settings.DB_FAKE_MIGRATE,
)

# #######################################################
# define global objects that may or may not be used by the actions
# #######################################################
cache = Cache(size=1000)
T = Translator(settings.T_FOLDER)

# #######################################################
# pick the session type that suits you best
# #######################################################
if settings.SESSION_TYPE == "cookies":
    session = Session(secret=settings.SESSION_SECRET_KEY)
elif settings.SESSION_TYPE == "redis":
    import redis

    host, port = settings.REDIS_SERVER.split(":")
    # for more options: https://github.com/andymccurdy/redis-py/blob/master/redis/client.py
    conn = redis.Redis(host=host, port=int(port))
    conn.set = (
        lambda k, v, e, cs=conn.set, ct=conn.ttl: cs(k, v, ct(k))
        if ct(k) >= 0
        else cs(k, v, e)
    )
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)
elif settings.SESSION_TYPE == "memcache":
    import memcache
    import time

    conn = memcache.Client(settings.MEMCACHE_CLIENTS, debug=0)
    session = Session(secret=settings.SESSION_SECRET_KEY, storage=conn)
elif settings.SESSION_TYPE == "database":
    from py4web.utils.dbstore import DBStore

    session = Session(secret=settings.SESSION_SECRET_KEY, storage=DBStore(db))

# #######################################################
# Instantiate the object and actions that handle auth
# #######################################################
auth = Auth(session, db, define_tables=False)

# Translate auth messages.
auth_messages = copy.deepcopy(auth.MESSAGES)

# Messages auth buttons
auth_messages["buttons"]["sign-in"] = T("Sing In")
auth_messages["buttons"]["sign-up"] = T("Sing Up")
auth_messages["buttons"]["lost-password"] = T("Lost Password")
auth_messages["buttons"]["register"] = T("Register")
auth_messages["buttons"]["request"] = T("Request")
auth_messages["buttons"]["submit"] = T("Submit")

# Mensajes de auth
auth_messages["verify_email"]["subject"] = T("Confirm email")
auth_messages["verify_email"]["body"] = T(
    "Welcome {first_name}, click {link} to confirm your email"
)
auth_messages["reset_password"]["subject"] = T("Password reset")
auth_messages["reset_password"]["body"] = T(
    "Hello {first_name}, click {link} to change password"
)
auth_messages["unsubscribe"]["subject"] = T("Unsubscribe confirmation")
auth_messages["unsubscribe"]["body"] = T(
    "By {first_name}, you have been erased from our system"
)

auth_messages["flash"]["user-registered"] = T("User registered")
auth_messages["flash"]["password-reset-link-sent"] = T("Password reset link sent")
auth_messages["flash"]["password-changed"] = T("Password changed")
auth_messages["flash"]["profile-saved"] = T("Profiled saved")
auth_messages["flash"]["user-logout"] = T("User logout")
auth_messages["flash"]["email-verified"] = T("Email verified")
auth_messages["flash"]["link-expired"] = T("Link expired")

auth_messages["labels"]["username"] = T("Username")
auth_messages["labels"]["email"] = T("Email")
auth_messages["labels"]["first_name"] = T("First Name")
auth_messages["labels"]["last_name"] = T("Last Name")
auth_messages["labels"]["phone_number"] = T("Phone Number")
auth_messages["labels"]["username_or_email"] = T("Username or Email")

auth_messages["labels"]["password"] = T("Password")
auth_messages["labels"]["new_password"] = T("New Password")
auth_messages["labels"]["old_password"] = T("Old Password")
auth_messages["labels"]["login_password"] = T("Password")
auth_messages["labels"]["password_again"] = T("Password (again)")
auth_messages["labels"]["created_on"] = T("Created On")
auth_messages["labels"]["created_by"] = T("Created By")
auth_messages["labels"]["modified_on"] = T("Modified On")
auth_messages["labels"]["modified_by"] = T("Modified By")


auth.param.messages = auth_messages

auth.use_username = True
auth.param.registration_requires_confirmation = settings.VERIFY_EMAIL
auth.param.registration_requires_approval = settings.REQUIRES_APPROVAL
auth.param.login_after_registration = settings.LOGIN_AFTER_REGISTRATION
auth.param.allowed_actions = settings.ALLOWED_ACTIONS
auth.param.login_expiration_time = 3600
auth.param.password_complexity = {"entropy": 50}
auth.param.block_previous_password_num = 3
auth.param.default_login_enabled = settings.DEFAULT_LOGIN_ENABLED
auth.define_tables()
auth.fix_actions()

flash = auth.flash

# #######################################################
# Configure email sender for auth
# #######################################################
if settings.SMTP_SERVER:
    auth.sender = Mailer(
        server=settings.SMTP_SERVER,
        sender=settings.SMTP_SENDER,
        login=settings.SMTP_LOGIN,
        tls=settings.SMTP_TLS,
        ssl=settings.SMTP_SSL,
    )

# #######################################################
# Create a table to tag users as group members
# #######################################################
if auth.db:
    groups = Tags(db.auth_user, "groups")

# #######################################################
# Enable optional auth plugin
# #######################################################
if settings.USE_PAM:
    from py4web.utils.auth_plugins.pam_plugin import PamPlugin

    auth.register_plugin(PamPlugin())

if settings.USE_LDAP:
    from py4web.utils.auth_plugins.ldap_plugin import LDAPPlugin

    auth.register_plugin(LDAPPlugin(db=db, groups=groups, **settings.LDAP_SETTINGS))

if settings.OAUTH2GOOGLE_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2google import OAuth2Google  # TESTED

    auth.register_plugin(
        OAuth2Google(
            client_id=settings.OAUTH2GOOGLE_CLIENT_ID,
            client_secret=settings.OAUTH2GOOGLE_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2google/callback",
        )
    )
if settings.OAUTH2FACEBOOK_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2facebook import OAuth2Facebook  # UNTESTED

    auth.register_plugin(
        OAuth2Facebook(
            client_id=settings.OAUTH2FACEBOOK_CLIENT_ID,
            client_secret=settings.OAUTH2FACEBOOK_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2facebook/callback",
        )
    )

if settings.OAUTH2OKTA_CLIENT_ID:
    from py4web.utils.auth_plugins.oauth2okta import OAuth2Okta  # TESTED

    auth.register_plugin(
        OAuth2Okta(
            client_id=settings.OAUTH2OKTA_CLIENT_ID,
            client_secret=settings.OAUTH2OKTA_CLIENT_SECRET,
            callback_url="auth/plugin/oauth2okta/callback",
        )
    )

# #######################################################
# Define a convenience action to allow users to download
# files uploaded and reference by Field(type='upload')
# #######################################################
if settings.UPLOAD_FOLDER:

    @action("download/<filename>")
    @action.uses(db)
    def download(filename):
        return downloader(db, settings.UPLOAD_FOLDER, filename)

    # To take advantage of this in Form(s)
    # for every field of type upload you MUST specify:
    #
    # field.upload_path = settings.UPLOAD_FOLDER
    # field.download_url = lambda filename: URL('download/%s' % filename)

# #######################################################
# Optionally configure celery
# #######################################################
if settings.USE_CELERY:
    from celery import Celery

    # to use "from .common import scheduler" and then use it according
    # to celery docs, examples in tasks.py
    scheduler = Celery(
        "apps.%s.tasks" % settings.APP_NAME, broker=settings.CELERY_BROKER
    )


# #######################################################
# Enable authentication
# #######################################################
auth.enable(uses=(session, T, db, Inject(T=T, session=session)), env=dict(T=T))

# #######################################################
# Define convenience decorators
# #######################################################
unauthenticated = ActionFactory(db, session, T, flash, auth)
authenticated = ActionFactory(db, session, T, flash, auth.user)
