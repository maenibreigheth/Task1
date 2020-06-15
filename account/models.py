from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin


class MyAccountManager(BaseUserManager):

    def create_user(self, email, first_name, last_name, gender, image=None, password=None):
        # Creates and save a new user

        if not email:
            raise ValueError("Users must have an email address")

        if not first_name:
            raise ValueError("Users must have a first name")

        if not last_name:
            raise ValueError("Users must have a last name")

        if not gender:
            raise ValueError("Users must specify a gender")

        if not password:
            raise ValueError("Users must have a password")

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            image=image,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, gender, password, image=None):
        # Creates and save a new superUser

        user = self.create_user(
            email,
            first_name,
            last_name,
            gender,
            image,
            password
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser, PermissionsMixin):
    # Choices for the gender field.
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]

    # Required Fields by default
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Our Own Fields
    email = models.EmailField(verbose_name='email', max_length=255, unique=True)
    password = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    image = models.ImageField(max_length=100, upload_to='uploads/')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password', 'first_name', 'last_name', 'gender']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
