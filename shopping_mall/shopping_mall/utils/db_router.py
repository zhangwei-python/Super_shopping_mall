# class MasterSlaveDBRouter(object):
#     """数据库读写路由"""
#     def db_for_read(self,model,**hints):
#         return "slave"
#
#     def db_for_write(self,model,**hints):
#         return "default"
#
#     def allow_relation(self,obj1,obj2,**hints):
#         return True