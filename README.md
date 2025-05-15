# Creative Contract Management API

## Overview
This API facilitates contract generation in the creative and events industry, connecting performers (musicians, dancers, photographers, etc.) with producers (venues, event organizers, video producers, etc.). The platform enables structured contract creation, event scheduling, and financial tracking.

## Features
- **User Registration**: Sign up and manage account details.
- **Profile Creation**: Performers & Producers define their services.
- **Contract Management**: Define agreements with Parties, Terms & Payment structure.
- **Event Organization**: Schedule events with details, Scheduling, locations, and contacts.
- **Accommodation Tracking**: Manage optional lodging details related to the event.

## Installation
To set up the API locally:
1. Clone the repository:
   ```bash
   git clone https://github.com/Gabosgit/MVP_backend_track_v1
   
2. Navigate to the project folder:
   ```bash
   cd MVP_backend_track_v1

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

4. Run the application:
   Local:
   ```bash
   fastapi dev main.py
   ```
   Remote:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 10000
   ```

### Set Up Environment Variables
   ```python
   SERVER_PWD=your_server_passowrd
   DATABASE_URL=e.g.= postgresql://postgres:password@localhost/postgres
   SECRET_KEY=your_secret_key  
   ALGORITHM=your_chosen_algorithm
   ```


# API Endpoints  
## User Management (pydantic)
POST /users/create → Register a new user.
   ```python
   class UserCreatePydantic(BaseModel):
      username: str
      type_of_entity: str
      password: str
      name: str
      surname: str
      email_address: EmailStr
      phone_number: str
      vat_id: Optional[str] = None
      bank_account: Optional[str] = None
   ```

## Profile Management
POST /profiles/create → Create a new profile. \
GET /profiles/{id} → Retrieve profile details.
   ```python
   class ProfilePydantic(BaseModel):
       name: str
       performance_type: str
       description: str
       bio: str
       social_media: List[Optional[HttpUrl]]
   ```





### API Documentation
Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc


