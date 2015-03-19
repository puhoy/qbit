__author__ = 'meatpuppet'

from PyQt4 import uic

if __name__ == '__main__':
    """ compiles the gui before running
    """
    uic.compileUiDir('gui')
    import qbit
    qbit.main()