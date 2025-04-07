%chk=545174.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(4,5)/cc-pVDZ gfinput fchk=all density=current iop(5/33=1) out=wfx

545174 beryllium_atom CASSCF(4,5) cc-pVDZ

0 1
Be    0.0000   0.0000   0.0000

545174.wfx

