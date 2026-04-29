import os, time
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in allowed_set

def save_file(file, folder, allowed_set):
    if file and file.filename != '' and allowed_file(file.filename, allowed_set):
        filename = f"{int(time.time())}_{secure_filename(file.filename)}"
        file.save(os.path.join(folder, filename))
        return filename
    return None
