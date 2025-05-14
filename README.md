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
   cd yourrepository

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

4. Run the application:
   ```bash
   fastapi dev main.py


# API Endpoints
## User Management (pydantic)
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


