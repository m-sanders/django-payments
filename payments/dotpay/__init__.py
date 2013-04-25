from .. import BasicProvider, get_payment_model
from .forms import ProcessPaymentForm
from django.http import HttpResponse, HttpResponseForbidden

Payment = get_payment_model()


class DotpayProvider(BasicProvider):
    '''
    dotpay.pl payment provider

    seller_id:
        seller ID, assigned by dotpay
    url:
        return URL, user will be bounced to this address after payment is
        processed
    pin:
        PIN
    channel:
        default payment channel (consult dotpay.pl reference guide)
    lang:
        UI language
    lock:
        whether to disable channels other than the default selected above
    '''
    _method = 'post'
    _action = 'https://ssl.dotpay.pl/'

    def __init__(self, *args, **kwargs):
        self._seller_id = kwargs.pop('seller_id')
        self._pin = kwargs.pop('pin')
        self._channel = kwargs.pop('channel', 0)
        self._lang = kwargs.pop('lang', 'pl')
        self._lock = kwargs.pop('lock', False)
        super(DotpayProvider, self).__init__(*args, **kwargs)

    def get_hidden_fields(self,):
        self.payment.save()
        description = '; '.join(['%(quantity)dx %(name)s (%(sku)s), '
                                 '%(price)f %(currency)s' % order._asdict()
                                 for order in self.order_items])
        data = {
            'id': self._seller_id,
            'amount': str(self.payment.total),
            'control': str(self.payment.id),
            'currency': self.payment.currency,
            'description': description,
            'lang': self._lang,
            'channel': str(self._channel),
            'ch_lock': '1' if self._lock else '0',
            'URL': self.payment.get_success_url(),
            'URLC': self.get_return_url(),
            'type': '2'
        }
        return data

    def process_data(self, request):
        form = ProcessPaymentForm(payment=self.payment, pin=self._pin,
                                  data=request.POST or None)
        if not form.is_valid():
            return HttpResponseForbidden('FAILED')
        form.save()
        return HttpResponse('OK')
