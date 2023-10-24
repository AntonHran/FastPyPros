import hashlib
from datetime import datetime
import requests

from fastapi.exceptions import HTTPException
from fastapi import status
import cloudinary
import cloudinary.api
import cloudinary.uploader

from src.conf.config import settings
from src.conf import messages


class CloudImage:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    @staticmethod
    def generate_file_name(username: str):
        created_at = datetime.now().strftime("%Y%m%d%H%M%S")
        name = hashlib.sha256(username.encode("utf-8")).hexdigest()[:12]
        return f"share_photo/{username}/{name}_{created_at}"

    @staticmethod
    def upload(file, public_id: str):
        """
        The upload function takes a file and public_id as arguments.
        The function then uploads the file to Cloudinary using the public_id provided.
        If no public_id is provided, one will be generated automatically.

        :param file: Specify the file to be uploaded
        :param public_id: str: Set the public id of the image
        :return: A dict with the following keys:
        :doc-author: Trelent
        """
        r = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
        return r

    @staticmethod
    def get_url_for_avatar(public_id, r):
        """
        The get_url_for_avatar function takes in a public_id and an r (which is the result of
        a cloudinary.api.resource call)
        and returns the URL for that avatar image, which will be used to display it on the page.

        :param public_id: Identify the image in cloudinary
        :param r: Get the version of the image
        :return: The url for the avatar image
        :doc-author: Trelent
        """
        src_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250,
                                                                  crop="fill", version=r.get("version"))
        return src_url

    @staticmethod
    def remove_image(username: str, public_id: str):
        cloudinary.uploader.destroy(f"photo_share/{username}/{public_id}", invalidate=True)

    @staticmethod
    def remove_folder(username):
        try:
            cloudinary.api.delete_folder(username)
        except BaseException:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NO_FOLDER)

    @staticmethod
    def get_file_by_url(public_id: str):
        resource = cloudinary.api.resource(public_id)
        file_url = resource['secure_url']
        response = requests.get(file_url)
        if response.status_code == 200:
            return response.content
