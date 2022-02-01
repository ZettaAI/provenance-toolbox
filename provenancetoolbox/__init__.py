__version__ = '0.1.0'

from . import process
from .process import Process, PythonGithubEnv, DockerEnv
from .process import logprocess, process_absent

from . import notebook
from .notebook import parsenotes, note_absent
from .notebook import addmotivation, addresult, addgeneric

from . import utils
from .utils import dockerimageID
