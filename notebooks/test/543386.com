%chk=543386.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

543386 beryllium_atom CASSCF(2,2) cc-pVDZ

0 1
Be    0.0000   0.0000   0.0000

543386.wfx

