%chk=CALC_000005.chk
%mem=4GB
%NProcShared=1
#P SP CISD/TZVP gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000005 ethene CISD TZVP

0 1
C        0.66900000    0.00000000    0.00000000
C       -0.66900000    0.00000000    0.00000000
H        1.23600000    0.93400000    0.00000000
H        1.23600000   -0.93400000    0.00000000
H       -1.23600000    0.93400000    0.00000000
H       -1.23600000   -0.93400000    0.00000000


CALC_000005.wfx

