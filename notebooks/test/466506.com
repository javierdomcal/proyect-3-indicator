%chk=466506.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) iop(4/21=100) out=wfx

466506 neon CASSCF(10,10) cc-pVDZ

0 1
Ne 0.0 0.0 0.0

466506.wfx

