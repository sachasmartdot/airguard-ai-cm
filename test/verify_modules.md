python3 -c "
import pandas as pd
import numpy as np
import sklearn
import xgboost as xgb
import lightgbm as lgb
import matplotlib
import seaborn
import yaml
print('pandas     :', pd.__version__)
print('numpy      :', np.__version__)
print('sklearn    :', sklearn.__version__)
print('xgboost    :', xgb.__version__)
print('lightgbm   :', lgb.__version__)
print('matplotlib :', matplotlib.__version__)
print('seaborn    :', seaborn.__version__)
print('pyyaml     : OK')
print()
print('✓ Tous les modules sont prêts — CPU only')
"
