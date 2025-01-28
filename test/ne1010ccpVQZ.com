%chk=ne1010ccpVQZ.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/cc-pVQZ gfinput fchk=all density=current iop(5/33=1) iop(4/21=100) out=wfx

ne1010ccpVQZ neon CASSCF(10,10) cc-pVQZ

0 1
Ne 0.0 0.0 0.0

ne1010ccpVQZ.wfx
