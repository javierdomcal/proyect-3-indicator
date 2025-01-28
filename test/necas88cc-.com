%chk=necas88cc-.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(8,8)/cc-pVTZ gfinput fchk=all density=current iop(5/33=1) out=wfx

necas88cc- neon CASSCF(8,8) cc-pVTZ

0 1
Ne 0.0 0.0 0.0

necas88cc-.wfx

