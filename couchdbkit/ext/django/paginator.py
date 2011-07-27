from django.core.paginator import Paginator as BasePaginator, Page

class Paginator(BasePaginator):
    def __init__(self, document_or_view, per_page, orphans=0, allow_empty_first_page=True):
        if hasattr(document_or_view, 'view'):
            self.view = lambda **kwargs: document_or_view.view('_all_docs', **kwargs)
        else:
            self.view = document_or_view
        self.per_page = per_page
        self.orphans = orphans
        self.allow_empty_first_page = allow_empty_first_page
        self._num_pages = self._count = None
    
    def _get_object_list(self, **kwargs):
        return self.view(**kwargs)
    
    def page(self, number):
        "Returns a Page object for the given 1-based page number."
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return Page(self._get_object_list(skip=bottom, limit=self.per_page), number, self)
    
    def _get_count(self):
        "Returns the total number of objects, across all pages."
        if self._count is None:
            result = self._get_object_list(limit=0)
            self._count = result.total_rows
        return self._count
    count = property(_get_count)

