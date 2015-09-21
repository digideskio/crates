'''
The idea here is this is a semi-transparent ORM gateway such that queries can
be built in a GET request. I'll see what can be factorised into a class. So
far, the JSON list streaming system has been, and the query system will be.
What remains is a flatten (to serialise) method for classes). Time, will tell.

'''
import json

from index.models import Album,AudioFile

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.http import FileResponse,HttpResponse

@login_required
def index(request):
    context = dict(
        title = "Hello!",
    )
    return render(request, 'crates/index.html', context)

# TODO: these parent classes belong in a separate module
class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class StreamingJsonView(View):
    def get(self, request):
        response = FileResponse(
            self._json_generator(),
            content_type="application/json"
        )

        return response

    def enumerate():
        'A generator of serialisable structures'
        raise NotImplementedError('Implement this in subclass')

    @staticmethod
    def _json_gen_wrapper(gen):
        for item in gen:
            yield json.dumps(item)

    def _json_generator(self):
        '''Manual JSON generator for streaming'''
        # JSON list out of arbitrary objects (json dump each object)
        gen = self.enumerate()

        gen = self._json_gen_wrapper(gen)

        try:
            yield '[%s' % next(gen)

            for ref in gen:
                yield ',\n%s' % ref

            yield ']'
        except StopIteration:
            yield '[]'

# TODO this is quite generic already -- should be a general model query API
class Albums(LoginRequiredMixin,StreamingJsonView):
    def enumerate(self):
        qs = Album.objects

        # TODO evaluate this from a security/performance perspective
        query = self.request.GET.dict()

        try:
            page = query.pop('page')
            page = int(page)
        except KeyError,ValueError:
            page = 0

        # magic key in query
        if 'order_by' in query:
            qs = qs.order_by( query.pop('order_by') )

        qs = qs.filter(**query)

        # how many items per page?
        stride = 100

        # todo pagination/infinite scroll
        for album in qs[page*stride:page*stride+stride]:
            #yield album.__dict__
            # TODO could be a flatten method for API
            yield {k:v for (k,v) in album.__dict__.iteritems() if not k.startswith('_')}


class AudioFilesView(LoginRequiredMixin,StreamingJsonView):
    def enumerate(self):
        qs = AudioFile.objects

        # TODO evaluate this from a security/performance perspective
        query = self.request.GET.dict()

        try:
            page = query.pop('page')
            page = int(page)
        except KeyError,ValueError:
            page = 0

        # magic key in query
        if 'order_by' in query:
            qs = qs.order_by( query.pop('order_by') )

        qs = qs.filter(**query)

        # how many items per page?
        stride = 100

        # todo pagination/infinite scroll
        for obj in qs[page*stride:page*stride+stride]:
            yield obj.flatten()
