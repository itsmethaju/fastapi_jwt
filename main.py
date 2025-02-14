from fastapi import FastAPI,Depends,HTTPException,status
import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model
from pydantic import BaseModel

app = FastAPI()

JWT_SECRET = 'secret'

class UserIn(BaseModel):
    username: str
    password: str
class User(Model):
    id =fields.IntField(pk=True)
    username = fields.CharField(50,unique=True)
    password_hash = fields.CharField(150)
    
    
    @classmethod
    async def get_user(cls,username):
        return cls.get(username = username)

    def verify_password(self,password):
        return bcrypt.verify(password,self.password_hash)
    
User_Pydantic = pydantic_model_creator(User,name='User')
UserIn_Pydantic = pydantic_model_creator(User,name='UserIn',exclude_readonly=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

class text(Model):
    id =fields.IntField(pk=True)
    username = fields.CharField(50,unique=True)
    password_hash = fields.CharField(150)
 
 
 

@app.post('/user',response_model=User_Pydantic)
async def create_user(user : UserIn): 
    user_obj = User(username = user.username,password_hash =bcrypt.hash(user.password))
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)
 
async def authenticate_user(username:str,password:str):
    user = await User.get(username=username)
    
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user
      
@app.post('/token')
async def generate_token(user : UserIn):
    user = await authenticate_user(user.username,user.password)
    
    if not user :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    
    user_obj = await User_Pydantic.from_tortoise_orm(user)
    
    token = jwt.encode(user_obj.dict(),JWT_SECRET)
    
    return{
        'access_token':token,
        'token_type':'beare'
    }
  
async def get_current_user(token:str = Depends(oauth2_scheme)):
    try :
        payload = jwt.decode(token, JWT_SECRET,algorithms=["HS256"])
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    return await User_Pydantic.from_tortoise_orm(user)
    

@app.get('/get_user',response_model=User_Pydantic)
async def get_user(user: UserIn = Depends(get_current_user)):
    return user
    
register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={'models':['main']},
    generate_schemas=True,
    add_exception_handlers=True
)
