import logging
from datetime import datetime, timedelta
from odoo.http import request

_logger = logging.getLogger(__name__)


class HandleResponse:

    @staticmethod
    def error_response(service, response=None, message=False, code=400, service_type=False):
        last = datetime.now()
        user_id = request.env.user.id
        _logger.warning('ldm transactions end at %s.', last)
        result = {
            'code': code,
            'success': False,
            'message': message,

        }
        if not message:
            message = "The Service (%s) already exist" % (service.get('name', False))
            result['default_code'] = service.get('default_code', False)
            result['message'] = message
        request.env.cr.execute(
            "INSERT INTO integration_log(request_date,create_date,create_uid,code, body, reason,service_type, active) VALUES ('%s', '%s','%s','%s', '%s', '%s','%s', True);" % (
                str(datetime.now()), str(datetime.now()), user_id, code, str(response).replace("'", ""), message,
                service_type))
        return result

    @staticmethod
    def success_response(service, message, reg_key, service_type=False):
        last = datetime.now()
        message_str = str(message).replace("{", "-").replace("}", "-").replace("'", "")
        user_id = request.env.user.id
        _logger.warning('ldm transactions end at %s.', last)
        request.env.cr.execute(
            "INSERT INTO integration_log(request_date,create_date ,create_uid,code, body,service_type, reason, active) VALUES ('%s','%s' ,'%s' ,'200', '%s','%s', '%s', True);" % (
                str(datetime.now()), str(datetime.now()), user_id,
                "reg_key: " + str(reg_key) + ' ' + str(service).replace("'", ""), service_type,
                message_str))

        return {
            "code": 200,
            "success": True,
            "default_code": service.get('default_code'),
            "message": message_str,
        }
