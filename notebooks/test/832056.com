%chk=832056.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

832056 ethene CASSCF(2,2) TZVP

0 1
C        0.66900000    0.00000000    0.00000000
C       -0.66900000    0.00000000    0.00000000
H        1.23600000    0.93400000    0.00000000
H        1.23600000   -0.93400000    0.00000000
H       -1.23600000    0.93400000    0.00000000
H       -1.23600000   -0.93400000    0.00000000

832056.wfx

