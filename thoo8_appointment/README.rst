Thoo8 Appointment Booking
=========================

Advanced Appointment Booking with Website Portal, Scheduling, and SMS OTP Verification

.. image:: static/description/icon.png
   :alt: Thoo8 Appointment Booking
   :align: center

Overview
--------
Thoo8 Appointment Booking is a comprehensive module for managing online appointments directly from the Odoo portal and website.
It offers advanced scheduling, verification, and SMS notifications to streamline the booking process and improve customer experience.

Key Features
------------
**1. Website Portal Booking**
- Book appointments directly from the portal.
- Support for scheduled appointments (date & time) or unscheduled requests.
- Service-based booking with gender-specific schedules (male, female, or both).
- Display service notes and available slots dynamically.

**2. Verification & Validation**
- Mobile OTP verification via SMS (Msegat integration).
- ID card validation (10 digits, starts with 1 or 2).
- Duplicate prevention: one active appointment per service per ID.
- Mobile number format validation (must start with 05 and 10 digits).

**3. Booking Restrictions**
- Global booking suspension option.
- Daily booking limits with automatic enforcement.
- Real-time check for available slots only.

**4. Backend Management**
- Full appointment lifecycle: Draft, Confirmed, Completed, Cancelled.
- Assign responsible users to appointments.
- Internal notes & cancellation reasons.
- Automatic slot management (mark booked/unbooked).
- Sequence-based unique appointment reference.

**5. SMS Notifications**
- Send SMS on appointment creation, confirmation, portal confirmation, and cancellation.
- Fully customizable SMS templates.
- Integrated with external SMS provider (Msegat via ``thoo8_sms_gateway``).

**6. Configuration & Settings**
- Enable/disable ID card or mobile OTP verification.
- Set daily booking limits and suspension rules.
- Manage service types, schedules, and slots from backend.
- Control SMS templates and settings from the configuration menu.

Benefits
--------
- Easy-to-use online booking system.
- Ensure data accuracy and avoid duplicate reservations.
- Automated notifications reduce manual communication.
- Flexible scheduling with gender-specific options.
- Fully integrated with Odoo portal, website, and backend.

Screenshots
-----------
.. image:: static/description/screenshot1.png
   :alt: Portal Booking Form
   :align: center

.. image:: static/description/screenshot2.png
   :alt: Appointment Backend View
   :align: center

.. image:: static/description/screenshot3.png
   :alt: SMS Configuration
   :align: center

Installation
------------
1. Download and install the module in your Odoo instance.
2. Ensure ``thoo8_sms_gateway`` is installed and configured for SMS integration.
3. Configure appointment settings under **Settings > Appointments**.
4. Customize SMS templates and service schedules as needed.

Support
-------
For support, customization, or inquiries:

- **Author:** Saleh Ibrahim - thoo8
- **Website:** http://www.thoo8.com
- **Email:** info@thoo8.com

