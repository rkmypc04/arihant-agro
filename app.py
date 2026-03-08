from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from functools import wraps
from datetime import datetime
import os
import json
from bson import ObjectId
from database.models import Database
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pdfkit
from number_to_words import convert_amount_words
from dotenv import load_dotenv
import logging
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'arihant-agro-secret-key-2024')
def format_inr(amount):
    amount = float(amount)
    s = f"{amount:.2f}"
    integer, decimal = s.split(".")

    if len(integer) > 3:
        last3 = integer[-3:]
        rest = integer[:-3]
        rest = ",".join([rest[max(i-2,0):i] for i in range(len(rest),0,-2)][::-1])
        integer = rest + "," + last3

    return integer + "." + decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Initialize database
db = Database()

# Create admin user (only if not exists)
db.create_admin_user()

# Company Information (Pre-filled from environment variables)
COMPANY_INFO = {
    'name': os.getenv('COMPANY_NAME', 'Arihant Agro Services'),
    'address': os.getenv('COMPANY_ADDRESS', 'Bus stop javal Khamgaon Road, Uday Nagar'),
    'proprietor': os.getenv('COMPANY_PROPRIETOR', 'Sanjay Patil'),
    'mobile': os.getenv('COMPANY_MOBILE', '9604373777'),
    'gstin': os.getenv('COMPANY_GSTIN', '27AAAAA0000A1Z5'),
    'bank_name': os.getenv('COMPANY_BANK', 'State Bank of India'),
    'branch': os.getenv('COMPANY_BRANCH', 'Khamgaon'),
    'account_no': os.getenv('COMPANY_ACCOUNT', '12345678901'),
    'ifsc': os.getenv('COMPANY_IFSC', 'SBIN0001234'),
    'email': os.getenv('COMPANY_EMAIL', 'info@arihantagro.com')
}

# Fixed Products with CML Numbers and Rates (Fallback)
FALLBACK_PRODUCTS = [
    {'id': 1, 'name': 'HDPE Pipes with Quick Release Coupler', 'cml_no': 'CML-001', 'rate': 45.00, 'unit': 'meter'},
    {'id': 2, 'name': 'QRC HDPE Service Saddle', 'cml_no': 'CML-002', 'rate': 125.00, 'unit': 'piece'},
    {'id': 3, 'name': 'Sprinkler Nozzles (Metal)', 'cml_no': 'CML-003', 'rate': 85.00, 'unit': 'piece'},
    {'id': 4, 'name': 'GI Riser Pipe 3/4"', 'cml_no': 'CML-004', 'rate': 320.00, 'unit': 'piece'},
    {'id': 5, 'name': 'QRC HDPE TEE', 'cml_no': 'CML-005', 'rate': 95.00, 'unit': 'piece'},
    {'id': 6, 'name': 'QRC HDPE Pump Connecting Nipple', 'cml_no': 'CML-006', 'rate': 145.00, 'unit': 'piece'},
    {'id': 7, 'name': 'QRC HDPE Bend with Coupler', 'cml_no': 'CML-007', 'rate': 110.00, 'unit': 'piece'},
    {'id': 8, 'name': 'QRC HDPE End Plug', 'cml_no': 'CML-008', 'rate': 55.00, 'unit': 'piece'},
    {'id': 9, 'name': 'Drip Irrigation Lateral Tube', 'cml_no': 'CML-009', 'rate': 28.00, 'unit': 'meter'},
    {'id': 10, 'name': 'Online Dripper (4 LPH)', 'cml_no': 'CML-010', 'rate': 3.50, 'unit': 'piece'},
    {'id': 11, 'name': 'Venturi Injector 3/4"', 'cml_no': 'CML-011', 'rate': 850.00, 'unit': 'piece'},
    {'id': 12, 'name': 'Screen Filter 2"', 'cml_no': 'CML-012', 'rate': 2450.00, 'unit': 'piece'}
]

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('कृपया लॉगिन करा', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('कृपया लॉगिन करा', 'warning')
            return redirect(url_for('login'))
        user = db.get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin', False):
            flash('प्रवेश निषिद्ध', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get product by ID (from DB or fallback)
def get_product_by_id(product_id):
    # Try database first
    try:
        product = db.get_product_by_id(product_id)
        if product:
            return product
    except Exception as e:
        app.logger.error(f"Error getting product from DB: {e}")
    
    # Fallback to FALLBACK_PRODUCTS list
    try:
        product = next((p for p in FALLBACK_PRODUCTS if str(p['id']) == str(product_id)), None)
        if product:
            return product
    except Exception as e:
        app.logger.error(f"Error getting product from fallback: {e}")
    
    return None

# Helper function to validate Indian mobile number
def validate_mobile(mobile):
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, mobile) is not None

# Helper function to validate email
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Routes
@app.route('/')
def home():
    return render_template('home.html', company=COMPANY_INFO)

@app.route('/about')
def about():
    return render_template('about.html', company=COMPANY_INFO)

@app.route('/services')
def services():
    return render_template('services.html', company=COMPANY_INFO)

@app.route('/products')
def products():
    try:
        db_products = db.get_all_products()
        display_products = db_products if db_products else FALLBACK_PRODUCTS
    except:
        display_products = FALLBACK_PRODUCTS
    return render_template('products.html', products=display_products, company=COMPANY_INFO)

@app.route('/brands')
def brands():
    try:
        all_brands = db.get_all_brands()
    except:
        all_brands = []
    return render_template('brands.html', company=COMPANY_INFO, brands=all_brands)

@app.route('/contact')
def contact():
    return render_template('contact.html', company=COMPANY_INFO)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', company=COMPANY_INFO)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        shop_name = request.form.get('shop_name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not all([name, shop_name, mobile, email, address, password]):
            flash('सर्व फील्ड भरणे आवश्यक आहे', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('पासवर्ड जुळत नाही', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('पासवर्ड किमान 6 अक्षरांचा असावा', 'danger')
            return redirect(url_for('register'))

        if not validate_mobile(mobile):
            flash('अवैध मोबाईल नंबर (10 अंकी, 6-9 ने सुरुवात)', 'danger')
            return redirect(url_for('register'))

        if not validate_email(email):
            flash('अवैध ईमेल पत्ता', 'danger')
            return redirect(url_for('register'))

        # Check if user exists
        if db.get_user_by_email(email):
            flash('हा ईमेल आधीच वापरात आहे', 'danger')
            return redirect(url_for('register'))

        if db.get_user_by_mobile(mobile):
            flash('हा मोबाईल नंबर आधीच वापरात आहे', 'danger')
            return redirect(url_for('register'))

        # Create user
        user_data = {
            'name': name,
            'shop_name': shop_name,
            'mobile': mobile,
            'email': email,
            'address': address,
            'password': generate_password_hash(password),
            'is_admin': False,
            'created_at': datetime.now(),
            'is_active': True
        }

        try:
            user_id = db.create_user(user_data)
            if user_id:
                flash('नोंदणी यशस्वी! कृपया लॉगिन करा', 'success')
                return redirect(url_for('login'))
            else:
                flash('नोंदणी अयशस्वी. पुन्हा प्रयत्न करा', 'danger')
        except Exception as e:
            app.logger.error(f"Registration error: {e}")
            flash('नोंदणी अयशस्वी. सर्वर त्रुटी', 'danger')

    return render_template('register.html', company=COMPANY_INFO)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('ईमेल आणि पासवर्ड भरणे आवश्यक आहे', 'danger')
            return redirect(url_for('login'))

        try:
            user = db.get_user_by_email(email)
            if user and check_password_hash(user['password'], password):
                if not user.get('is_active', True):
                    flash('तुमचे खाते निष्क्रिय केले गेले आहे. प्रशासकाशी संपर्क साधा.', 'danger')
                    return redirect(url_for('login'))
                
                session.permanent = True
                session['user_id'] = str(user['_id'])
                session['user_name'] = user['name']
                session['is_admin'] = user.get('is_admin', False)
                session['last_login'] = datetime.now().isoformat()
                
                flash('लॉगिन यशस्वी!', 'success')
                
                if user.get('is_admin', False):
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                flash('अवैध ईमेल किंवा पासवर्ड', 'danger')
        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash('लॉगिन अयशस्वी. सर्वर त्रुटी', 'danger')

    return render_template('login.html', company=COMPANY_INFO)

@app.route('/logout')
def logout():
    session.clear()
    flash('लॉगआउट यशस्वी', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user_id = session['user_id']
        quotations = db.get_user_quotations(user_id)
        user = db.get_user_by_id(user_id)
        
        # Calculate statistics
        total_quotations = len(quotations)
        draft_quotations = sum(1 for q in quotations if q.get('status') == 'draft')
        saved_quotations = sum(1 for q in quotations if q.get('status') == 'saved')
        
        stats = {
            'total': total_quotations,
            'draft': draft_quotations,
            'saved': saved_quotations
        }
        
        return render_template('dashboard.html', 
                             company=COMPANY_INFO, 
                             quotations=quotations, 
                             user=user,
                             stats=stats)
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        flash('डॅशबोर्ड लोड करताना त्रुटी', 'danger')
        return redirect(url_for('home'))

@app.route('/quotation/new', methods=['GET', 'POST'])
@login_required
def new_quotation():
    if request.method == 'POST':
        try:
            # Get customer details
            customer_data = {
                'name': request.form.get('customer_name', '').strip(),
                'mobile': request.form.get('customer_mobile', '').strip(),
                'gaon': request.form.get('gaon', '').strip(),
                'shivar': request.form.get('shivar', '').strip(),
                'gat_no': request.form.get('gat_no', '').strip(),
                'shetra': request.form.get('shetra', '').strip(),
                'taluka': request.form.get('taluka', '').strip(),
                'jilha': request.form.get('jilha', '').strip(),
                'aadhar': request.form.get('aadhar', '').strip(),
                'shetkari_id': request.form.get('shetkari_id', '').strip()
            }

            brand = request.form.get('brand', '')

            # Get items
            items = []
            total_amount = 0
            product_ids = request.form.getlist('product_id[]')
            sizes = request.form.getlist('size[]')
            quantities = request.form.getlist('quantity[]')
            rate_list = request.form.getlist('rate[]') if session.get('is_admin') else []

            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i] and float(quantities[i]) > 0:
                    product = get_product_by_id(product_ids[i])
                    if product:
                        quantity = float(quantities[i])
                        rate = float(product.get('rate', 0))
                        
                        # Only admin allowed to override rate
                        if session.get('is_admin') and i < len(rate_list) and rate_list[i]:
                            rate = float(rate_list[i])
                        
                        amount = rate * quantity
                        
                        items.append({
                            'product_id': str(product.get('_id', product.get('id'))),
                            'product_name': product['name'],
                            'cml_no': product.get('cml_no', ''),
                            'size': sizes[i] if i < len(sizes) else '',
                            'quantity': quantity,
                            'unit': product.get('unit', 'piece'),
                            'rate': rate,
                            'amount': amount
                        })
                        total_amount += amount

            if not items:
                flash('किमान एक उत्पादन निवडा', 'danger')
                return redirect(url_for('new_quotation'))

            # Calculate totals
            discount_percent = float(request.form.get('discount', 0) or 0)
            discount_amount = (total_amount * discount_percent) / 100
            taxable_amount = total_amount - discount_amount
            cgst = (taxable_amount * 2.5) / 100
            sgst = (taxable_amount * 2.5) / 100
            gst_total = cgst + sgst
            grand_total = taxable_amount + gst_total
            round_off = round(grand_total) - grand_total
            final_amount = round(grand_total)

            # Convert to words
            amount_in_words, amount_in_words_marathi = convert_amount_words(final_amount)

            quotation_data = {
                'user_id': session['user_id'],
                'quotation_no': db.get_next_quotation_number(),
                'date': datetime.now(),
                'customer': customer_data,
                'brand': brand,
                'items': items,
                'sub_total': round(total_amount, 2),
                'discount_percent': discount_percent,
                'discount_amount': round(discount_amount, 2),
                'taxable_amount': round(taxable_amount, 2),
                'cgst': round(cgst, 2),
                'sgst': round(sgst, 2),
                'gst_total': round(gst_total, 2),
                'grand_total': round(grand_total, 2),
                'round_off': round(round_off, 2),
                'final_amount': final_amount,
                'amount_in_words': amount_in_words,
                'amount_in_words_marathi': amount_in_words_marathi,
                'status': 'draft',
                'created_at': datetime.now()
            }

            quotation_id = db.create_quotation(quotation_data)
            if quotation_id:
                flash('कोटेशन तयार झाले', 'success')
                return redirect(url_for('quotation_preview', quotation_id=str(quotation_id)))
            else:
                flash('कोटेशन तयार करण्यात अयशस्वी', 'danger')
        except Exception as e:
            app.logger.error(f"Quotation creation error: {e}")
            flash('कोटेशन तयार करताना त्रुटी', 'danger')

    # GET request - show form
    try:
        db_products = db.get_all_products()
        all_products = db_products if db_products else FALLBACK_PRODUCTS
        
        # Convert ObjectId to string for products
        for product in all_products:
            if '_id' in product:
                product['_id'] = str(product['_id'])
        
        brands = db.get_all_brands()
        for brand in brands:
            if '_id' in brand:
                brand['_id'] = str(brand['_id'])
    except Exception as e:
        app.logger.error(f"Error loading form data: {e}")
        all_products = FALLBACK_PRODUCTS
        brands = []

    return render_template('quotation_form.html', 
                         company=COMPANY_INFO, 
                         products=all_products, 
                         brands=brands)

@app.route('/quotation/preview/<quotation_id>')
@login_required
def quotation_preview(quotation_id):
    try:
        quotation = db.get_quotation_by_id(quotation_id)
        if not quotation:
            flash('कोटेशन सापडले नाही', 'danger')
            return redirect(url_for('dashboard'))

        # Check if user owns this quotation or is admin
        if str(quotation['user_id']) != session['user_id'] and not session.get('is_admin', False):
            flash('प्रवेश निषिद्ध', 'danger')
            return redirect(url_for('dashboard'))

        # Get brand details if any
        brand = None
        if quotation.get("brand"):
            try:
                brand = db.get_brand_by_id(quotation["brand"])
                if brand:
                    quotation['brand_name'] = brand.get("name", "")
                    quotation['brand_company'] = brand.get("company_name", "")
                    quotation['brand_details'] = brand.get("company_details", "")
                    quotation['brand_products'] = brand.get("products", "")
                    quotation['brand_logo'] = brand.get("logo", "")
            except:
                pass

        if not brand:
            quotation['brand_name'] = quotation.get('brand', '')
            quotation['brand_company'] = ''
            quotation['brand_details'] = ''
            quotation['brand_products'] = ''
            quotation['brand_logo'] = ''

        return render_template('quotation_preview.html', 
                             company=COMPANY_INFO, 
                             quotation=quotation)
    except Exception as e:
        app.logger.error(f"Quotation preview error: {e}")
        flash('कोटेशन प्रीव्यू लोड करताना त्रुटी', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/quotation/download/<quotation_id>')
@login_required
def download_quotation(quotation_id):
    try:
        quotation = db.get_quotation_by_id(quotation_id)
        if not quotation:
            flash('कोटेशन सापडले नाही', 'danger')
            return redirect(url_for('dashboard'))

        # Check if user owns this quotation or is admin
        if str(quotation['user_id']) != session['user_id'] and not session.get('is_admin', False):
            flash('प्रवेश निषिद्ध', 'danger')
            return redirect(url_for('dashboard'))

        # Get brand details if any
        brand = None
        if quotation.get("brand"):
            try:
                brand = db.get_brand_by_id(quotation.get("brand"))
                if brand:
                    quotation['brand_name'] = brand.get("name", "")
                    quotation['brand_company'] = brand.get("company_name", "")
                    quotation['brand_details'] = brand.get("company_details", "")
                    quotation['brand_products'] = brand.get("products", "")
                    quotation['brand_logo'] = brand.get("logo", "")
            except:
                pass

        # Update status to saved
        db.update_quotation_status(quotation_id, 'saved')

        # Generate HTML for PDF
        rendered = render_template('quotation_preview.html', 
                           company=COMPANY_INFO, 
                           quotation=quotation)

        # Create PDFs directory if not exists
        pdf_dir = os.path.join(app.root_path, "pdfs", "quotations")
        try:
            os.makedirs(pdf_dir, exist_ok=True)
        except Exception as e:
            app.logger.error(f"Error creating directory: {e}")

        pdf_filename = f"quotation_{quotation.get('quotation_no', 'quotation').replace('/', '_')}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        # Try to generate PDF
        pdf_generated = False
        try:
            # Configure pdfkit options
            options = {
                'page-size': 'A4',
                'margin-top': '5mm',
                'margin-right': '8mm',
                'margin-bottom': '8mm',
                'margin-left': '8mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }

            # Check if wkhtmltopdf path is configured
            wkhtmltopdf_path = os.getenv("WKHTMLTOPDF_PATH")
            if wkhtmltopdf_path and os.path.exists(wkhtmltopdf_path):
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                pdfkit.from_string(rendered, pdf_path, options=options, configuration=config)
            else:
                # Try without custom configuration
                pdfkit.from_string(rendered, pdf_path, options=options)
            
            pdf_generated = True
            flash('PDF तयार झाले', 'success')
        except Exception as e:
            app.logger.error(f'PDF generation error: {e}')
            flash('PDF तयार करण्यात त्रुटी, HTML डाउनलोड करत आहे', 'warning')

        if pdf_generated and os.path.exists(pdf_path):
            # Return PDF file
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            response = make_response(pdf_content)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename={pdf_filename}'
            return response
        else:
            # Fallback to HTML download
            response = make_response(rendered)
            response.headers['Content-Type'] = 'text/html'
            response.headers['Content-Disposition'] = f'attachment; filename=quotation_{quotation.get("quotation_no", "quotation").replace("/", "_")}.html'
            return response

    except Exception as e:
        app.logger.error(f"Download error: {e}")
        flash('डाउनलोड करताना त्रुटी', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        stats = db.get_admin_statistics()
        recent_quotations = db.get_all_quotations(limit=50)
        users = db.get_all_users()
        product_count = len(db.get_all_products())
        
        return render_template('admin_dashboard.html', 
                             company=COMPANY_INFO, 
                             stats=stats, 
                             quotations=recent_quotations, 
                             users=users, 
                             product_count=product_count)
    except Exception as e:
        app.logger.error(f"Admin dashboard error: {e}")
        flash('डॅशबोर्ड लोड करताना त्रुटी', 'danger')
        return redirect(url_for('home'))

@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required
def admin_products():
    if request.method == 'POST':
        try:
            product_data = {
                'name': request.form.get('name', '').strip(),
                'cml_no': request.form.get('cml_no', '').strip(),
                'rate': float(request.form.get('rate', 0)),
                'unit': request.form.get('unit', 'piece').strip(),
                'created_at': datetime.now()
            }
            
            if not product_data['name'] or not product_data['cml_no'] or product_data['rate'] <= 0:
                flash('सर्व फील्ड योग्यरित्या भरा', 'danger')
            else:
                db.create_product(product_data)
                flash('उत्पादन यशस्वीरित्या जोडले', 'success')
        except Exception as e:
            app.logger.error(f"Product creation error: {e}")
            flash('उत्पादन जोडताना त्रुटी', 'danger')
        
        return redirect(url_for('admin_products'))

    try:
        products = db.get_all_products()
        # Convert ObjectId to string for each product
        for product in products:
            if '_id' in product:
                product['_id'] = str(product['_id'])
    except Exception as e:
        app.logger.error(f"Error loading products: {e}")
        products = []

    return render_template('admin_products.html', products=products, company=COMPANY_INFO)

@app.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    if request.method == 'POST':
        try:
            update_data = {
                'name': request.form.get('name', '').strip(),
                'cml_no': request.form.get('cml_no', '').strip(),
                'rate': float(request.form.get('rate', 0)),
                'unit': request.form.get('unit', 'piece').strip()
            }
            
            if not update_data['name'] or not update_data['cml_no'] or update_data['rate'] <= 0:
                flash('सर्व फील्ड योग्यरित्या भरा', 'danger')
            else:
                db.update_product(product_id, update_data)
                flash('उत्पादन यशस्वीरित्या अद्यतनित केले', 'success')
                return redirect(url_for('admin_products'))
        except Exception as e:
            app.logger.error(f"Product update error: {e}")
            flash('उत्पादन अद्यतनित करताना त्रुटी', 'danger')

    try:
        product = db.get_product_by_id(product_id)
        if product and '_id' in product:
            product['_id'] = str(product['_id'])
    except Exception as e:
        app.logger.error(f"Error loading product: {e}")
        product = None

    if not product:
        flash('उत्पादन सापडले नाही', 'danger')
        return redirect(url_for('admin_products'))

    return render_template('edit_product.html', product=product, company=COMPANY_INFO)

@app.route('/admin/products/delete/<product_id>')
@admin_required
def delete_product(product_id):
    try:
        if db.delete_product(product_id):
            flash('उत्पादन हटवले गेले', 'success')
        else:
            flash('उत्पादन हटवण्यात त्रुटी', 'danger')
    except Exception as e:
        app.logger.error(f"Product deletion error: {e}")
        flash('उत्पादन हटवताना त्रुटी', 'danger')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/brands', methods=['GET', 'POST'])
@admin_required
def admin_brands():
    if request.method == 'POST':
        try:
            logo = request.files.get("logo")
            logo_filename = ""
            
            if logo and logo.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in logo.filename and logo.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    logo_filename = secure_filename(logo.filename)
                    # Ensure directory exists
                    upload_path = os.path.join(app.root_path, "static", "images", "brands")
                    os.makedirs(upload_path, exist_ok=True)
                    logo.save(os.path.join(upload_path, logo_filename))
                else:
                    flash('अवैध फाइल प्रकार. फक्त PNG, JPG, JPEG, GIF परवानगी', 'danger')
                    return redirect(url_for("admin_brands"))

            brand_data = {
                "name": request.form.get("name", "").strip(),
                "company_name": request.form.get("company_name", "").strip(),
                "company_details": request.form.get("company_details", "").strip(),
                "products": request.form.get("products", "").strip(),
                "logo": logo_filename,
                "created_at": datetime.now()
            }
            
            if not brand_data['name'] or not brand_data['company_name']:
                flash('कंपनीचे नाव आणि ब्रँड नाव आवश्यक आहे', 'danger')
            else:
                db.create_brand(brand_data)
                flash("ब्रँड यशस्वीरित्या जोडला", "success")
        except Exception as e:
            app.logger.error(f"Brand creation error: {e}")
            flash("ब्रँड जोडताना त्रुटी", "danger")
        
        return redirect(url_for("admin_brands"))

    try:
        brands = db.get_all_brands()
        # Convert ObjectId to string for each brand
        for brand in brands:
            if '_id' in brand:
                brand['_id'] = str(brand['_id'])
    except Exception as e:
        app.logger.error(f"Error loading brands: {e}")
        brands = []

    return render_template('admin_brands.html', brands=brands, company=COMPANY_INFO)

@app.route('/admin/brands/delete/<brand_id>')
@admin_required
def delete_brand(brand_id):
    try:
        if db.delete_brand(brand_id):
            flash('ब्रँड हटवला गेला', 'success')
        else:
            flash('ब्रँड हटवण्यात त्रुटी', 'danger')
    except Exception as e:
        app.logger.error(f"Brand deletion error: {e}")
        flash('ब्रँड हटवताना त्रुटी', 'danger')
    
    return redirect(url_for('admin_brands'))

@app.route('/admin/kits', methods=['GET', 'POST'])
@admin_required
def admin_kits():
    if request.method == 'POST':
        try:
            selected_products = request.form.getlist('product_id')
            items = []
            
            for product_id in selected_products:
                qty = request.form.get(f'qty_{product_id}')
                if qty and int(qty) > 0:
                    items.append({
                        'product_id': product_id,
                        'qty': int(qty)
                    })
            
            if not items:
                flash('किमान एक उत्पादन निवडा', 'danger')
                return redirect(url_for('admin_kits'))
            
            kit_data = {
                'brand_id': request.form.get('brand_id', ''),
                'kit_name': request.form.get('kit_name', '').strip(),
                'size': request.form.get('size', '').strip(),
                'items': items,
                'created_at': datetime.now()
            }
            
            if not kit_data['kit_name'] or not kit_data['brand_id']:
                flash('किटचे नाव आणि ब्रँड आवश्यक आहे', 'danger')
            else:
                db.create_kit(kit_data)
                flash('किट यशस्वीरित्या जोडले', 'success')
        except Exception as e:
            app.logger.error(f"Kit creation error: {e}")
            flash('किट जोडताना त्रुटी', 'danger')
        
        return redirect(url_for('admin_kits'))

    try:
        # Convert ObjectId to string for brands and products
        brands = db.get_all_brands()
        for brand in brands:
            if '_id' in brand:
                brand['_id'] = str(brand['_id'])
        
        kits_products = db.get_all_products()
        for product in kits_products:
            if '_id' in product:
                product['_id'] = str(product['_id'])
        
        kits = db.get_all_kits()
    except Exception as e:
        app.logger.error(f"Error loading kits data: {e}")
        brands = []
        kits_products = []
        kits = []

    return render_template('admin_kits.html', 
                         brands=brands, 
                         kits=kits, 
                         kits_products=kits_products, 
                         company=COMPANY_INFO)

@app.route('/admin/kits/delete/<kit_id>')
@admin_required
def delete_kit(kit_id):
    try:
        if db.delete_kit(kit_id):
            flash('किट हटवले गेले', 'success')
        else:
            flash('किट हटवण्यात त्रुटी', 'danger')
    except Exception as e:
        app.logger.error(f"Kit deletion error: {e}")
        flash('किट हटवताना त्रुटी', 'danger')
    
    return redirect(url_for('admin_kits'))

@app.route('/admin/quotations')
@admin_required
def admin_all_quotations():
    try:
        quotations = db.get_all_quotations()
        return render_template('admin_all_quotations.html', 
                             quotations=quotations, 
                             company=COMPANY_INFO)
    except Exception as e:
        app.logger.error(f"Error loading quotations: {e}")
        flash('कोटेशन लोड करताना त्रुटी', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/api/get-product/<product_id>')
@login_required
def get_product_api(product_id):
    try:
        product = get_product_by_id(product_id)
        if product:
            return jsonify({
                'id': str(product.get('_id', product.get('id'))),
                'name': product['name'],
                'cml_no': product.get('cml_no', ''),
                'rate': float(product.get('rate', 0)),
                'unit': product.get('unit', 'piece')
            })
    except Exception as e:
        app.logger.error(f"API error: {e}")
    
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/get-kits-by-brand/<brand_id>')
@login_required
def get_kits_by_brand(brand_id):
    try:
        kits = db.get_kits_by_brand(brand_id)
        kit_list = []
        for kit in kits:
            kit_list.append({
                "_id": str(kit["_id"]),
                "name": kit.get("kit_name", ""),
                "size": kit.get("size", "")
            })
        return jsonify(kit_list)
    except Exception as e:
        app.logger.error(f"API error: {e}")
        return jsonify([])

@app.route('/api/get-kit/<kit_id>')
@login_required
def get_kit(kit_id):
    try:
        kit = db.get_kit_by_id(kit_id)
        if not kit:
            return jsonify({'error': 'Kit not found'}), 404

        final_items = []
        for item in kit.get('items', []):
            # get product from DB by ID
            product = db.get_product_by_id(item.get('product_id'))
            if product:
                final_items.append({
                    'product_id': str(product['_id']),
                    'product_name': product['name'],
                    'cml_no': product.get('cml_no', ''),
                    'rate': float(product.get('rate', 0)),
                    'unit': product.get('unit', 'piece'),
                    'quantity': item.get('qty', 1)
                })

        return jsonify({
            'kit_name': kit.get('kit_name', ''),
            'size': kit.get('size', ''),
            'items': final_items
        })
    except Exception as e:
        app.logger.error(f"API error: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/calculate-quotation', methods=['POST'])
@login_required
def calculate_quotation():
    try:
        data = request.json
        items = data.get('items', [])
        discount_percent = float(data.get('discount', 0) or 0)

        total_amount = 0
        for item in items:
            product = get_product_by_id(item['product_id'])
            if product:
                total_amount += float(product.get('rate', 0)) * float(item.get('quantity', 1))

        discount_amount = (total_amount * discount_percent) / 100
        taxable_amount = total_amount - discount_amount
        cgst = (taxable_amount * 2.5) / 100
        sgst = (taxable_amount * 2.5) / 100
        gst_total = cgst + sgst
        grand_total = taxable_amount + gst_total
        round_off = round(grand_total) - grand_total
        final_amount = round(grand_total)

        amount_in_words, amount_in_words_marathi = convert_amount_words(final_amount)

        return jsonify({
            'sub_total': round(total_amount, 2),
            'discount_amount': round(discount_amount, 2),
            'taxable_amount': round(taxable_amount, 2),
            'cgst': round(cgst, 2),
            'sgst': round(sgst, 2),
            'gst_total': round(gst_total, 2),
            'grand_total': round(grand_total, 2),
            'round_off': round(round_off, 2),
            'final_amount': round(final_amount, 2),
            'amount_in_words': amount_in_words,
            'amount_in_words_marathi': amount_in_words_marathi
        })
    except Exception as e:
        app.logger.error(f"Calculation error: {e}")
        return jsonify({'error': 'Calculation failed'}), 500

@app.route('/quotation/delete/<quotation_id>')
@login_required
def delete_quotation(quotation_id):
    try:
        quotation = db.get_quotation_by_id(quotation_id)
        if not quotation:
            flash('Quotation सापडले नाही', 'danger')
            return redirect(url_for('dashboard'))

        if str(quotation['user_id']) != session['user_id'] and not session.get('is_admin'):
            flash('Permission नाही', 'danger')
            return redirect(url_for('dashboard'))

        db.delete_quotation(quotation_id)
        flash('Quotation हटवले गेले', 'success')
    except Exception as e:
        app.logger.error(f"Quotation deletion error: {e}")
        flash('Quotation हटवताना त्रुटी', 'danger')
    
    return redirect(url_for('dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', company=COMPANY_INFO), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', company=COMPANY_INFO), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)