from celery_tasks.main import celery_app
from celery_tasks.yuntongxun.sms import CCP

@celery_app.task(name="ccp_send_msg_code")
def ccp_send_msg_code(mobile,msg_code):

    return CCP().send_template_sms(mobile,[msg_code,5],1)