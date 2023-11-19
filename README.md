PhotoShare

Brief description of the project.

## Basic REST API functionality based on FastAPI

- Authentication using JWT tokens for roles: user, moderator, administrator.
- Download, delete, edit photos by users.
- Upload, delete, edit photo descriptions by users.
- Adding and using tags for photos.
- Basic operations with photos using the Cloudinary service.
- Creation of links to transformed images from URL and QR-code.
- Commenting on photos, editing comments by users.
- User profiles, editing of own information.
- Ban users by administrators.
- Photo rating, restrictions on rating your photos.
- Search and filter photos by keyword, tag, rating and date.

## Additional functionality

- User verification mechanism via e-mail during registration.
- Added a cover.
- The user exit mechanism from the application via logout.
- Photo rating and viewing for moderators and administrators.
- Search and filter photos by users who added them.
- A separate account (personal account) for each user where his personal data is stored.

## Technical details

- The application was deployed to the Koyeb cloud service, link: https://fastpypros-photoshare-p-fastpypros.koyeb.app/
- 90% coverage of the application with unit tests.