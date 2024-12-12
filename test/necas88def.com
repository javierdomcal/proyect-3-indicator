%chk=necas88def.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(8,8)/def2-TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

necas88def neon CASSCF(8,8) def2-TZVP

0 1
Ne 0.0 0.0 0.0

necas88def.wfx

