from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
from PIL import Image, ImageEnhance, ImageOps

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './static/uploads'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def apply_brightness_contrast(input_img, brightness, contrast):
    enhancer = ImageEnhance.Brightness(input_img)
    img_brightness = enhancer.enhance(brightness)

    enhancer = ImageEnhance.Contrast(img_brightness)
    img_contrast = enhancer.enhance(contrast)

    return img_contrast

def apply_rotate(input_img, rotate):
    return input_img.rotate(rotate, expand=True)

def apply_mirror(input_img, horizontal, vertical):
    if horizontal:
        input_img = ImageOps.mirror(input_img)
    if vertical:
        input_img = ImageOps.flip(input_img)
    
    return input_img

def apply_scaling(input_img, scale_factor):
    width, height = input_img.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    return input_img.resize((new_width, new_height))

def apply_translation(input_img, x_translation, y_translation):
    return input_img.transform(input_img.size, Image.AFFINE, (1, 0, x_translation, 0, 1, y_translation))

def reset_image(original_path, edited_path):
    original_img = Image.open(original_path)
    original_img.save(edited_path)

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            # Simpan versi asli
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], 'original_' + uploaded_file.filename)
            try:
                uploaded_file.save(file_path)
                Image.open(file_path).verify()  # Memeriksa apakah file valid
                uploaded_file.seek(0)
                uploaded_file.save(original_path)
            except Exception as e:
                return f"File upload failed: {e}", 400

            return redirect(url_for('edit', filename=uploaded_file.filename))
    return redirect(url_for('home'))

@app.route('/edit/<filename>')
def edit(filename):
    return render_template('edit.html', filename=filename)

@app.route('/process/<filename>', methods=['POST'])
def process(filename):
    if request.method == 'POST':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return f"File {filename} not found", 404

        try:
            edited_img = Image.open(file_path)
        except Exception as e:
            return f"Failed to open image: {e}", 400
        
        brightness = float(request.form.get('brightness', 1.0))
        contrast = float(request.form.get('contrast', 1.0))
        rotate = int(request.form.get('rotate', 0))
        horizontal = bool(request.form.get('horizontal'))
        vertical = bool(request.form.get('vertical'))
        scale_factor = float(request.form.get('scale', 1.0))
        x_translation = int(request.form.get('translate_x', 0))
        y_translation = int(request.form.get('translate_y', 0))

        edited_img = apply_brightness_contrast(edited_img, brightness, contrast)
        edited_img = apply_rotate(edited_img, rotate)
        edited_img = apply_mirror(edited_img, horizontal, vertical)
        edited_img = apply_scaling(edited_img, scale_factor)
        edited_img = apply_translation(edited_img, x_translation, y_translation)

        edited_img.save(file_path)

        return redirect(url_for('uploaded_file', filename=filename))

@app.route('/reset/<filename>')
def reset(filename):
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], 'original_' + filename)
    edited_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(original_path):
        reset_image(original_path, edited_path)
        return redirect(url_for('edit', filename=filename))
    else:
        return f"Original image for {filename} not found", 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/save_image/<filename>', methods=['POST'])
def save_image(filename):
    edited_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    saved_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'saved_' + filename)

    try:
        # Simpan gambar yang sudah diedit dengan nama baru
        edited_img = Image.open(edited_path)
        edited_img.save(saved_image_path)

        # Beri tautan URL untuk gambar yang disimpan
        saved_image_url = url_for('uploaded_file', filename='saved_' + filename, _external=True)

        return jsonify({'success': True, 'saved_image_url': saved_image_url})
    except Exception as e:
        print(e)
        return jsonify({'success': False})
    
if __name__ == '__main__':
    app.run(debug=True)
