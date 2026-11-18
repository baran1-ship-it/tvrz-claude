// Úchop nástroje v pěsti (three.js r128) – výňatek ze hry Hvozd. Prsty sevře animace UAL, nástroj se jen usadí do pěsti.
const bp=(n,v)=>HB.bones[n].getWorldPosition(v);
function handAxes(sd){bp('index_01_'+sd,gL);bp('pinky_01_'+sd,gT);gK.addVectors(gL,gT).multiplyScalar(.5);gL.sub(gT).normalize();bp('hand_'+sd,gW);gF.subVectors(gK,gW);gF.addScaledVector(gL,-gF.dot(gL)).normalize()}
// nástroj v pěsti podle animace (Quaternius UAL, prsty sevřené animátorem): topůrko napříč dlaní, ostří ve směru kloubů
function gripTool(obj,sd,spin=0,slant=.3){const B=HB.bones;if(!B['index_01_'+sd])return;
  handAxes(sd);bp('middle_02_'+sd,gD3);bp('ring_02_'+sd,gT);gD3.add(gT).multiplyScalar(.5);gC.copy(gK).add(gD3).multiplyScalar(.5);
  gB.copy(gL).addScaledVector(gF,slant).normalize();tZ.copy(gF).addScaledVector(gB,-gF.dot(gB)).normalize();tX.crossVectors(gB,tZ).normalize();
  gM.makeBasis(tX,gB,tZ);obj.quaternion.setFromRotationMatrix(gM);if(spin)obj.rotateY(spin);obj.position.copy(gC)}
