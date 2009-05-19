from datetime import datetime
from tg import expose, validate, flash, require, url, request, redirect
from sqlalchemy import and_, or_
from sqlalchemy.orm import eagerload
from webhelpers import paginate

from mediaplex.lib.base import BaseController
from mediaplex.lib.helpers import expose_xhr
from mediaplex.model import DBSession, Media, Video, Comment, Tag

class AdminController(BaseController):
    """Admin dashboard actions"""

    @expose_xhr('mediaplex.templates.admin.index','mediaplex.templates.admin.video.dash-table')
    def index(self, **kwargs):
        if request.is_xhr:
            """ShowMore Ajax Fetch Action"""
            status = kwargs.get('status', 'pending_review')
            page_num = kwargs.get('page_num', 1)
            return dict(collection=self._fetch_page(status, page_num).items)
        else:
            # Any publishable video that does have a publish_on date that is in the
            # past and is publishable is 'Recently Published'
            recent_media = DBSession.query(Media).\
                filter(Media.status.intersects('publish')).\
                filter(Media.publish_on < datetime.now).\
                order_by(Media.publish_on)[:5]
            comments_pending_review = DBSession.query(Comment).filter(Comment.status >= 'pending_review').count()
            comments_total = DBSession.query(Comment).count()

            return dict(review_page=self._fetch_page('pending_review'),
                        encode_page=self._fetch_page('pending_encoding'),
                        publish_page=self._fetch_page('draft'),
                        num_comments_to_review=comments_pending_review,
                        num_comments_total=comments_total,
                        recent_media=recent_media)

    def _fetch_page(self, status='pending_review', page_num=1, items_per_page=6):
        """Helper method for paginating media results"""
        query = DBSession.query(Media).\
            filter(Video.status.intersects(status)).\
            filter(Video.status.excludes('trash')).\
            order_by(Video.created_on)

        return paginate.Page(query, page_num, items_per_page)

