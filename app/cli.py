import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError


cli = typer.Typer()

@cli.command()
def initialize():
    """
    Initializes the database by dropping existing tables, 
    recreating them, and adding a default 'bob' user.
    """
    with get_session() as db:
        drop_all()
        create_db_and_tables()
        bob = User(username='bob', email='bob@mail.com', password='bobpass')
        db.add(bob)
        db.commit()
        db.refresh(bob)
        print("Database Initialized")

@cli.command()
def get_user(
    username: str = typer.Argument(..., help="The exact username of the user to retrieve.")
):
    """
    Retrieves and prints a single user from the database by their username.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """
    Retrieves and prints all users currently stored in the database.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def change_email(
    username: str = typer.Argument(..., help="The username of the account to update."),
    new_email: str = typer.Argument(..., help="The new email address to assign to the user.")
):
    """
    Updates the email address of an existing user.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: str = typer.Argument(..., help="The desired username (must be unique)."),
    email: str = typer.Argument(..., help="The user's email address (must be unique)."),
    password: str = typer.Argument(..., help="The raw password, which will be hashed.")
):
    """
    Creates a new user account in the database. Fails gracefully if 
    the username or email already exists.
    """
    with get_session() as db:
        newuser = User(username=username, email=email, password=password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print("Username or email already taken!")
        else:
            print(newuser)

@cli.command()
def delete_user(
    username: str = typer.Argument(..., help="The username of the account to be deleted.")
):
    """
    Deletes a user from the database entirely.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

#  EXERCISES 1 and 2

@cli.command()
def search_user(
    query: str = typer.Argument(..., help="The partial username or email to search for.")
):
    """
    Find a user using a partial match of their email OR username.
    """
    with get_session() as db:
        users = db.exec(
            select(User).where(
                (User.username.contains(query)) | (User.email.contains(query))
            )
        ).all()
        
        if not users:
            print(f"No users found matching '{query}'.")
        else:
            for user in users:
                print(user)

@cli.command()
def list_users(
    limit: int = typer.Argument(10, help="The maximum number of users to return."),
    offset: int = typer.Argument(0, help="The number of users to skip.")
):
    """
    List the first N users of the database to be used by a paginated table.
    """
    with get_session() as db:
        users = db.exec(select(User).offset(offset).limit(limit)).all()
        
        if not users:
            print("No users found.")
        else:
            for user in users:
                print(user)

if __name__ == "__main__":
    cli()