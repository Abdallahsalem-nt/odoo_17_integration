import logging


import werkzeug
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.utils

from odoo import models,http
from odoo.http import request
from odoo.exceptions import AccessDenied, AccessError, MissingError

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    # @classmethod
    # def _authenticate(cls, endpoint):
    #
    #     auth_method = endpoint.routing["auth"]
    #     if endpoint.routing.get('special_param'):
    #         return auth_method
    #         auth_method = 'none'
    #     # if request._is_cors_preflight(endpoint):
    #     auth_method = 'none'
    #     try:
    #         if request.session.uid:
    #             try:
    #                 request.session.check_security()
    #                 # what if error in security.check()
    #                 #   -> res_users.check()
    #                 #   -> res_users._check_credentials()
    #             except (AccessDenied, http.SessionExpiredException):
    #                 # All other exceptions mean undetermined status (e.g. connection pool full),
    #                 # let them bubble up
    #                 request.session.logout(keep_db=True)
    #         if request.uid is None:
    #             getattr(cls, "_auth_method_%s" % auth_method)()
    #     except (AccessDenied, http.SessionExpiredException, werkzeug.exceptions.HTTPException):
    #         raise
    #     except Exception:
    #         _logger.info("Exception during request Authentication.", exc_info=True)
    #
    #         raise AccessDenied()
    #     return auth_method