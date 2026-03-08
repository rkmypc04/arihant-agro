from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from datetime import datetime
import os
from werkzeug.security import generate_password_hash

class Database:
    def __init__(self):
        # Get MongoDB URI from environment variable or use local
        self.mongodb_uri = os.environ.get(
            "MONGO_URI",
            os.environ.get("MONGODB_URI", "mongodb://localhost:27017/arihant_agro")
        )
        
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)

            # Test connection
            self.client.admin.command("ping")

            self.db = self.client["arihant_agro"]

            # Initialize collections
            self.users = self.db.users
            self.quotations = self.db.quotations
            self.products = self.db.products
            self.brands = self.db.brands
            self.kits = self.db.kits

            # Create indexes
            self.users.create_index('email', unique=True)
            self.users.create_index('mobile', unique=True)
            self.quotations.create_index('quotation_no', unique=True)
            
            print("MongoDB connected successfully!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            # Fallback to in-memory storage for development
            self.users = []
            self.quotations = []
            self.products = []
            self.brands = []
            self.kits = []
            self._user_counter = 0
            self._quotation_counter = 0
            self._product_counter = 0
            self._brand_counter = 0
            self._kit_counter = 0
    
    # User Operations
    def create_user(self, user_data):
        try:
            if isinstance(self.users, list):
                self._user_counter += 1
                user_data['_id'] = str(self._user_counter)
                self.users.append(user_data)
                return user_data['_id']
            else:
                result = self.users.insert_one(user_data)
                return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        try:
            if isinstance(self.users, list):
                return next((u for u in self.users if u['_id'] == user_id), None)
            return self.users.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    
    def get_user_by_email(self, email):
        try:
            if isinstance(self.users, list):
                return next((u for u in self.users if u.get('email') == email), None)
            return self.users.find_one({'email': email})
        except:
            return None
    
    def get_user_by_mobile(self, mobile):
        try:
            if isinstance(self.users, list):
                return next((u for u in self.users if u.get('mobile') == mobile), None)
            return self.users.find_one({'mobile': mobile})
        except:
            return None
    
    def get_all_users(self):
        try:
            if isinstance(self.users, list):
                return self.users
            return list(self.users.find())
        except:
            return []
    
    # Create admin user
    def create_admin_user(self):
        admin_data = {
            'name': 'Admin',
            'shop_name': 'Arihant Agro Services',
            'mobile': '9604373737',
            'email': 'admin@arihantagro.com',
            'address': 'Bus stop javal Khamgaon Road, Uday Nagar',
            'password': generate_password_hash('admin123'),
            'is_admin': True,
            'created_at': datetime.now()
        }

        try:
            if isinstance(self.users, list):
                existing = next((u for u in self.users if u.get('email') == admin_data['email']), None)
                if not existing:
                    self._user_counter += 1
                    admin_data['_id'] = str(self._user_counter)
                    self.users.append(admin_data)
                    print("Admin user created successfully!")
            else:
                if not self.users.find_one({'email': admin_data['email']}):
                    self.users.insert_one(admin_data)
                    print("Admin user created successfully!")
        except Exception as e:
            print(f"Error creating admin user: {e}")
    
    # Quotation Operations
    def create_quotation(self, quotation_data):
        try:
            if isinstance(self.quotations, list):
                self._quotation_counter += 1
                quotation_data['_id'] = str(self._quotation_counter)
                self.quotations.append(quotation_data)
                return quotation_data['_id']
            else:
                result = self.quotations.insert_one(quotation_data)
                return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating quotation: {e}")
            return None
    
    def get_quotation_by_id(self, quotation_id):
        try:
            if isinstance(self.quotations, list):
                return next((q for q in self.quotations if q['_id'] == quotation_id), None)
            return self.quotations.find_one({'_id': ObjectId(quotation_id)})
        except:
            return None
    
    def get_user_quotations(self, user_id):
        try:
            if isinstance(self.quotations, list):
                return [q for q in self.quotations if str(q.get('user_id')) == user_id]
            return list(self.quotations.find({'user_id': user_id}).sort('date', DESCENDING))
        except:
            return []
    
    def get_all_quotations(self, limit=None):
        try:
            if isinstance(self.quotations, list):
                quotations = sorted(self.quotations, key=lambda x: x.get('date', datetime.min), reverse=True)
                return quotations[:limit] if limit else quotations
            cursor = self.quotations.find().sort('date', DESCENDING)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except:
            return []
    
    def update_quotation_status(self, quotation_id, status):
        try:
            if isinstance(self.quotations, list):
                for q in self.quotations:
                    if q['_id'] == quotation_id:
                        q['status'] = status
                        return True
                return False
            result = self.quotations.update_one(
                {'_id': ObjectId(quotation_id)},
                {'$set': {'status': status}}
            )
            return result.modified_count > 0
        except:
            return False
    
    def delete_quotation(self, quotation_id):
        try:
            if isinstance(self.quotations, list):
                self.quotations = [q for q in self.quotations if q['_id'] != quotation_id]
                return True
            else:
                result = self.quotations.delete_one({'_id': ObjectId(quotation_id)})
                return result.deleted_count > 0
        except:
            return False
    
    def get_next_quotation_number(self):
        try:
            if isinstance(self.quotations, list):
                if not self.quotations:
                    return 'QTN-0001'
                max_num = max(int(q.get('quotation_no', 'QTN-0000').split('-')[1]) for q in self.quotations)
                return f'QTN-{max_num + 1:04d}'
            
            last_quotation = self.quotations.find_one(sort=[('quotation_no', DESCENDING)])
            if last_quotation and 'quotation_no' in last_quotation:
                last_num = int(last_quotation['quotation_no'].split('-')[1])
                return f'QTN-{last_num + 1:04d}'
            return 'QTN-0001'
        except:
            return 'QTN-0001'
    
    # Admin Statistics
    def get_admin_statistics(self):
        try:
            if isinstance(self.users, list):
                total_users = len([u for u in self.users if not u.get('is_admin', False)])
                total_quotations = len(self.quotations)
                today = datetime.now().date()
                today_quotations = len([q for q in self.quotations 
                                      if q.get('date') and hasattr(q.get('date'), 'date') and q.get('date').date() == today])
                
                return {
                    'total_users': total_users,
                    'total_quotations': total_quotations,
                    'today_quotations': today_quotations
                }
            
            total_users = self.users.count_documents({'is_admin': {'$ne': True}})
            total_quotations = self.quotations.count_documents({})
            
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_quotations = self.quotations.count_documents({'date': {'$gte': today_start}})
            
            return {
                'total_users': total_users,
                'total_quotations': total_quotations,
                'today_quotations': today_quotations
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_users': 0,
                'total_quotations': 0,
                'today_quotations': 0
            }
    
    # Product Operations
    def get_all_products(self):
        """Get all active products"""
        try:
            if isinstance(self.products, list):
                return [p for p in self.products if p.get('active', True)]
            return list(self.products.find({'active': True}))
        except Exception as e:
            print(f"Error getting products: {e}")
            return []
    
    def create_product(self, data):
        """Create a new product"""
        try:
            data['active'] = True
            data['created_at'] = datetime.now()
            
            if isinstance(self.products, list):
                self._product_counter += 1
                data['_id'] = str(self._product_counter)
                self.products.append(data)
                return data['_id']
            else:
                result = self.products.insert_one(data)
                return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating product: {e}")
            return None
    
    def get_product_by_id(self, pid):
        """Get product by ID"""
        try:
            if isinstance(self.products, list):
                return next((p for p in self.products if p['_id'] == pid), None)
            return self.products.find_one({'_id': ObjectId(pid)})
        except Exception as e:
            print(f"Error getting product: {e}")
            return None
    
    def update_product(self, pid, data):
        """Update product details"""
        try:
            if isinstance(self.products, list):
                for p in self.products:
                    if p['_id'] == pid:
                        p.update(data)
                        return True
                return False
            else:
                result = self.products.update_one(
                    {'_id': ObjectId(pid)},
                    {'$set': data}
                )
                return result.modified_count > 0
        except Exception as e:
            print(f"Error updating product: {e}")
            return False
    
    def delete_product(self, pid):
        """Soft delete product (set active=False)"""
        try:
            return self.update_product(pid, {'active': False})
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
    
    # Brand Operations
    def get_all_brands(self):
        """Get all active brands"""
        try:
            if isinstance(self.brands, list):
                return [b for b in self.brands if b.get('active', True)]
            return list(self.brands.find({'active': True}))
        except Exception as e:
            print(f"Error getting brands: {e}")
            return []
    
    def create_brand(self, data):
        """Create a new brand"""
        try:
            brand_data = {
                'name': data.get('name'),
                'company_name': data.get('company_name', ''),
                'company_details': data.get('company_details', ''),
                'products': data.get('products', ''),
                'logo': data.get('logo', ''),
                'active': True,
                'created_at': datetime.now()
            }
            
            if isinstance(self.brands, list):
                self._brand_counter += 1
                brand_data['_id'] = str(self._brand_counter)
                self.brands.append(brand_data)
                return brand_data['_id']
            else:
                result = self.brands.insert_one(brand_data)
                return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating brand: {e}")
            return None
    
    def get_brand_by_id(self, brand_id):
        """Get brand by ID"""
        try:
            if isinstance(self.brands, list):
                return next((b for b in self.brands if b['_id'] == brand_id), None)
            return self.brands.find_one({'_id': ObjectId(brand_id)})
        except Exception as e:
            print(f"Error getting brand: {e}")
            return None
    
    def update_brand(self, brand_id, data):
        """Update brand details"""
        try:
            if isinstance(self.brands, list):
                for b in self.brands:
                    if b['_id'] == brand_id:
                        b.update(data)
                        return True
                return False
            else:
                result = self.brands.update_one(
                    {'_id': ObjectId(brand_id)},
                    {'$set': data}
                )
                return result.modified_count > 0
        except Exception as e:
            print(f"Error updating brand: {e}")
            return False
    
    def delete_brand(self, brand_id):
        """Soft delete brand (set active=False)"""
        try:
            if isinstance(self.brands, list):
                for b in self.brands:
                    if b['_id'] == brand_id:
                        b['active'] = False
                        return True
                return False
            else:
                result = self.brands.update_one(
                    {'_id': ObjectId(brand_id)},
                    {'$set': {'active': False}}
                )
                return result.modified_count > 0
        except Exception as e:
            print(f"Error deleting brand: {e}")
            return False

    # Kit Operations
    def create_kit(self, kit_data):
        """Create a new kit"""
        try:
            kit_data['created_at'] = datetime.now()
            # FIX: convert brand_id to ObjectId
            if 'brand_id' in kit_data:
                try:
                    kit_data['brand_id'] = ObjectId(kit_data['brand_id'])
                except:
                    pass
            if isinstance(self.kits, list):
                self._kit_counter += 1
                kit_data['_id'] = str(self._kit_counter)
                self.kits.append(kit_data)
                return kit_data['_id']
            else:
                result = self.kits.insert_one(kit_data)
                return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating kit: {e}")
            return None

    def get_kits_by_brand(self, brand_id):
        """Get all kits for a specific brand"""
        try:
            if isinstance(self.kits, list):
                return [k for k in self.kits if k.get('brand_id') == brand_id]
            return list(self.kits.find({'brand_id': ObjectId(brand_id)}))
        except Exception as e:
            print(f"Error getting kits: {e}")
            return []

    def get_kit_by_id(self, kit_id):
        """Get kit by ID"""
        try:
            if isinstance(self.kits, list):
                return next((k for k in self.kits if k['_id'] == kit_id), None)
            return self.kits.find_one({'_id': ObjectId(kit_id)})
        except Exception as e:
            print(f"Error getting kit: {e}")
            return None

    def update_kit(self, kit_id, data):
        """Update kit details"""
        try:
            if isinstance(self.kits, list):
                for k in self.kits:
                    if k['_id'] == kit_id:
                        k.update(data)
                        return True
                return False
            else:
                result = self.kits.update_one(
                    {'_id': ObjectId(kit_id)},
                    {'$set': data}
                )
                return result.modified_count > 0
        except Exception as e:
            print(f"Error updating kit: {e}")
            return False

    def delete_kit(self, kit_id):
        """Delete a kit"""
        try:
            if isinstance(self.kits, list):
                self.kits = [k for k in self.kits if k['_id'] != kit_id]
                return True
            else:
                result = self.kits.delete_one({'_id': ObjectId(kit_id)})
                return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting kit: {e}")
            return False

    def get_all_kits(self):
        """Get all kits"""
        try:
            if isinstance(self.kits, list):
                return self.kits
            return list(self.kits.find())
        except Exception as e:
            print(f"Error getting all kits: {e}")
            return []