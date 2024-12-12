%chk=necas88aug-cc-.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(8,8)/aug-cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

necas88aug-cc- neon CASSCF(8,8) aug-cc-pVQZ

0 1
Ne 0.0 0.0 0.0

necas88aug-cc-.wfx

