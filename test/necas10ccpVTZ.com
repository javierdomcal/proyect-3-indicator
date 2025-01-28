%chk=necas10ccpVTZ.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/cc-pVTZ gfinput fchk=all density=current iop(5/33=1) iop(4/21=100) out=wfx

necas10ccpVTZ neon CASSCF(10,10) cc-pVTZ

0 1
Ne 0.0 0.0 0.0

necas10ccpVTZ.wfx

