import os
from celery import Celery
from rembg import remove
import io
from PIL import Image

celery_app = Celery('tasks', backend='redis://localhost', broker='pyamqp://root:ows123@localhost/testvhost1')

@celery_app.task(bind=True)
def remove_bg(self, image):
    try:
        bg_removed = remove(image)
        Image.open(io.BytesIO(bg_removed)).save(os.path.join('removed', f'{self.request.id}.png'))
        return True
    except:
        return False