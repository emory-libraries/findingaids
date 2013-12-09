# file findingaids/content/models.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import glob
import os

from django.conf import settings

# At load time, generate a list of available banner images
# for display on the home page
banner_path = os.path.join(settings.BASE_DIR, 'content', 'static', 'images', 'banner')
extensions = ['jpg', 'png']

BANNER_IMAGES = []
for ext in extensions:
    BANNER_IMAGES.extend([os.path.basename(f) for f in
                          glob.glob(os.path.join(banner_path, '*.%s' % ext))])


