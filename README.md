# Arihant Agro Services

A professional, fully functional website for Arihant Agro Services - an agriculture-based shop selling drip irrigation, sprinkler systems, HDPE pipes, plumbing materials, machinery, sanitary and bathroom fittings.

## Features

### Public Pages
- **Home**: Attractive landing page with company info, services, products, and testimonials
- **About Us**: Company information, mission, vision, and owner details
- **Services**: Detailed service offerings with process explanation
- **Products**: Product catalog with filtering by category
- **Brands**: Authorized dealer information for major brands
- **Contact**: Contact form, company details, map, and bank information
- **Privacy Policy**: Comprehensive privacy policy

### User Features
- **Registration**: User registration with name, shop name, mobile, email, and address
- **Login**: Secure login system with password hashing
- **Dashboard**: User dashboard to view and manage quotations
- **Quotation System**: 
  - Create professional quotations with pre-filled company info
  - Customer details: Name, Mobile, Gaon, Shivar, Gat No., Shetra, Taluka, Jilha, Aadhar, Shetkari ID
  - Brand selection from dropdown
  - 12 fixed agriculture products with CML numbers and rates
  - Auto-calculation: Subtotal, Discount, GST (CGST 2.5% + SGST 2.5%), Round-off, Final Amount
  - Amount in words (Marathi)
  - Professional A4 printable format with signature spaces
  - Save and Download as PDF
  - Print functionality

### Admin Features
- **Admin Dashboard**: Statistics, recent quotations, user management
- **View all quotations**: See all quotations created by users
- **User management**: View all registered users
- **Export**: Export quotations to Excel/CSV

## Technology Stack

- **Backend**: Python Flask
- **Database**: MongoDB (with fallback to in-memory for development)
- **Frontend**: HTML5, CSS3, JavaScript
- **CSS Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Poppins, Noto Sans Devanagari)

## Installation

### Prerequisites
- Python 3.8+
- MongoDB (optional, falls back to in-memory storage)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/arihant-agro.git
cd arihant-agro
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (optional):
```bash
export SECRET_KEY="your-secret-key"
export MONGODB_URI="mongodb://localhost:27017/arihant_agro"
```

5. Run the application:
```bash
python app.py
```

6. Open in browser:
```
http://localhost:5000
```

### Default Admin Credentials
- **Email**: admin@arihantagro.com
- **Password**: admin123

## Deployment

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app`
5. Add environment variables:
   - `SECRET_KEY`: Your secret key
   - `MONGODB_URI`: Your MongoDB Atlas connection string

### MongoDB Atlas Setup

1. Create a free cluster on MongoDB Atlas
2. Create a database user
3. Whitelist your IP address
4. Get the connection string
5. Add to environment variables

## Project Structure

```
arihant-agro/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── static/                # Static files
│   ├── css/
│   │   └── style.css     # Custom CSS
│   ├── js/
│   │   └── quotation.js  # JavaScript for quotations
│   └── images/           # Images and logos
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── home.html        # Home page
│   ├── about.html       # About page
│   ├── services.html    # Services page
│   ├── products.html    # Products page
│   ├── brands.html      # Brands page
│   ├── contact.html     # Contact page
│   ├── privacy.html     # Privacy policy
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── dashboard.html   # User dashboard
│   ├── quotation_form.html      # Quotation creation form
│   ├── quotation_preview.html   # Quotation preview
│   ├── admin_dashboard.html     # Admin dashboard
│   ├── 404.html         # 404 error page
│   └── 500.html         # 500 error page
├── pdfs/
│   └── quotations/      # Generated PDF quotations
└── database/
    └── models.py        # Database models
```

## Company Information

- **Name**: Arihant Agro Services
- **Address**: Bus stop javal Khamgaon Road, Uday Nagar
- **Proprietor**: Vaibhav Belokar
- **Mobile**: 9604373737 / 9860989891
- **GSTIN**: 27ATSPB7925Q1ZS
- **Bank**: State Bank of India, Branch Undri
- **Account No**: 39330999201
- **IFSC**: SBIN0003955

## Authorized Brands

- Jain Irrigation Systems Ltd
- Supreme
- Praytag
- PSG
- Sona
- Finolex

## License

This project is proprietary and confidential.

## Support

For support, contact:
- Email: arihantagro@gmail.com
- Phone: 9604373737 / 9860989891
