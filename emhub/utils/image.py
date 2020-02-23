# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab.se) [1]
# *
# * [1] SciLifeLab, Stockholm University
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'delarosatrevin@scilifelab.se'
# *
# **************************************************************************

import io
import base64
from PIL import Image


def fn_to_base64(filename):
    """ Read the image filename as a PIL image
    and encode it as base64.
    """
    try:
        img = Image.open(filename)
        encoded = pil_to_base64(img)
        img.close()
    except:
        encoded = ''
    return encoded


def pil_to_base64(pil_img):
    """ Encode as base64 the PIL image to be
    returned as an AJAX response.
    """
    img_io = io.BytesIO()
    pil_img.save(img_io, format='PNG')
    return base64.b64encode(img_io.getvalue()).decode("utf-8")
