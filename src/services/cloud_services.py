import cloudinary
import cloudinary.uploader
import base64
import io


from src.conf.config import settings

class TransformImage:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    @staticmethod
    async def upload_image(
        file: UploadFile,
        folder: str = None,
        effect: str = None,
        border: str = None,
        radius: str = None):
        """
        Function of applying effects to the image.

        :param: Image name
        :param: Folder name to save the image
        :param: Overlaying effects on a image provided by the cloudinary service
        :param: Creating a frame around a image
        :param: Transformation of a image into an ellipse or circle
        :return: URL of the image with superimposed effects
        :doc-author: Trelent
        """
        with file.file as input_file:
            transform_image_url = cloudinary.uploader.upload(input_file, folder=folder, effect=effect, border=border, radius=radius)

        return transform_image_url

    @staticmethod
    async def qrcode_image(transform_image_url):
        """
        The function converts the URL address of the transformed image into a QR code.
        The function converts the received qr code to a base64 string

        :param transform_image_url:
        :return: base64 string
        :doc-author: Trelent
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=7,
            border=2,
        )
        qr.add_data(transform_image_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        img_bytes = io.BytesIO()
        qr_img.save(img_bytes, format='PNG')
        qr_img_bytes = img_bytes.getvalue()

        qr_image_base64 = base64.b64encode(qr_img_bytes).decode('utf-8')
        return qr_image_base64