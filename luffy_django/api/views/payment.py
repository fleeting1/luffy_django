from rest_framework.views import APIView
from rest_framework.response import Response
from utils.auth import LuffyAuth
from django.conf import settings
from django_redis import get_redis_connection
import json
from utils.response import BaseResponse
from api import models
import datetime

class PaymentViewSet(APIView):
    authentication_classes =  [LuffyAuth,]
    conn = get_redis_connection("default")
    def post(self,request,*args,**kwargs):
        ret = BaseResponse()
        try:
            payment_dict = {}

            global_coupon_dict = {
                "coupon":{},
                "default_coupon":0
            }

            # 1. 获取用户要结算课程ID
            course_id_list = request.data.get('courseids')
            for course_id in course_id_list:
                car_key = settings.SHOPPING_CAR_KEY %(request.auth.user_id,course_id,)

                # 1.1 检测用户要结算的课程是否已经加入购物车
                if not self.conn.exists(car_key):
                    ret.code = 1001
                    ret.error = "课程需要先加入购物车才能结算"
                # 1.2 从购物车中获取信息，放入到结算中心。
                # 获取标题和图片
                policy = json.loads(self.conn.hget(car_key, 'policy').decode('utf-8'))
                default_policy = self.conn.hget(car_key, 'default_policy').decode('utf-8')
                policy_info = policy[default_policy]

                payment_course_dict = {
                    "title":self.conn.hget(car_key, 'title').decode('utf-8'),
                    "img":self.conn.hget(car_key, 'img').decode('utf-8'),
                    "policy_id":default_policy,
                    "coupon":{},
                    "default_coupon":0
                }
                payment_course_dict.update(policy_info)
                payment_dict[str(course_id)] = payment_course_dict


            # 2. 获取优惠券
            ctime = datetime.date.today()

            coupon_list = models.CouponRecord.objects.filter(
                account=request.auth.user,
                status=0,
                coupon__valid_begin_date__lte=ctime,
                coupon__valid_end_date__gte=ctime,
            )


            for item in coupon_list:


                # 只处理绑定课程的优惠券
                if not item.coupon.object_id:
                    # 优惠券ID
                    coupon_id = item.id

                    # 优惠券类型：满减、折扣、立减
                    coupon_type = item.coupon.coupon_type

                    info = {}
                    info['coupon_type'] = coupon_type
                    info['coupon_display'] = item.coupon.get_coupon_type_display()
                    if coupon_type == 0:  # 立减
                        info['money_equivalent_value'] = item.coupon.money_equivalent_value
                    elif coupon_type == 1:  # 满减券
                        info['money_equivalent_value'] = item.coupon.money_equivalent_value
                        info['minimum_consume'] = item.coupon.minimum_consume
                    else:  # 折扣
                        info['off_percent'] = item.coupon.off_percent

                    global_coupon_dict['coupon'][coupon_id] = info

                    continue
                # 优惠券绑定课程的ID
                coupon_course_id = str(item.coupon.object_id)

                # 优惠券ID
                coupon_id = item.id

                # 优惠券类型：满减、折扣、立减
                coupon_type = item.coupon.coupon_type

                info = {}
                info['coupon_type'] = coupon_type
                info['coupon_display'] = item.coupon.get_coupon_type_display()
                if coupon_type == 0: # 立减
                    info['money_equivalent_value'] = item.coupon.money_equivalent_value
                elif coupon_type == 1: # 满减券
                    info['money_equivalent_value'] = item.coupon.money_equivalent_value
                    info['minimum_consume'] = item.coupon.minimum_consume
                else: # 折扣
                    info['off_percent'] = item.coupon.off_percent

                if coupon_course_id not in payment_dict:
                    # 获取到优惠券，但是没有购买此课程
                    continue
                # 将优惠券设置到指定的课程字典中
                payment_dict[coupon_course_id]['coupon'][coupon_id] = info


            # 可以获取绑定的优惠券
            print(payment_dict)
            print(global_coupon_dict)

            # 3. 将绑定优惠券课程+全站优惠券 写入到redis中（结算中心）。



        except Exception as e:
            pass

        return Response(ret.dict)
